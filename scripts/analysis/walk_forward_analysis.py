#!/usr/bin/env python3
"""
Walk-Forward Analysis for ML Trading Strategy
=============================================
"""

import argparse
import json
import logging
import pickle
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

# Core imports
from src.ml.training.feature_engineering import FeatureConfig, FeatureEngineer
from src.ml.training.labeling import TripleBarrierConfig, TripleBarrierLabeler, RegimeAwareBarrierLabeler

# Try to import ML libraries
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    xgb = None

try:
    import lightgbm as lgb
    LGB_AVAILABLE = True
except ImportError:
    LGB_AVAILABLE = False
    lgb = None

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


class WalkForwardAnalysis:
    def __init__(
        self,
        data_path: str = "user_data/data/binance",
        models_dir: str = "user_data/models/walk_forward",
        results_dir: str = "user_data/walk_forward_results",
        use_dynamic_barriers: bool = True,
    ):
        self.data_path = Path(data_path)
        self.models_dir = Path(models_dir)
        self.results_dir = Path(results_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.window_results = []
        self.cumulative_pnl = []
        self.equity_curve = []
        # CRITICAL FIX: enforce_stationarity=False because it replaces 'close' with log_cumsum 
        # but leaves 'open' raw, breaking intraday_return and other OHLC features.
        self.feature_config = FeatureConfig(
            scale_features=True, 
            scaling_method="standard", 
            remove_correlated=True,
            enforce_stationarity=False 
        )
        # Reduced barriers for MFT/Scalping logic (1.5% TP / 0.75% SL)
        self.label_config = TripleBarrierConfig(take_profit=0.015, stop_loss=0.0075, max_holding_period=24)
        if use_dynamic_barriers:
            logger.info("Using RegimeAwareBarrierLabeler (Dynamic ATR Barriers)")
            self.labeler = RegimeAwareBarrierLabeler(self.label_config)
        else:
            self.labeler = TripleBarrierLabeler(self.label_config)

    def load_data(self, pair: str, timeframe: str = "5m") -> pd.DataFrame:
        pair_filename = pair.replace("/", "_")
        possible_paths = [
            self.data_path / f"{pair_filename}-{timeframe}.feather",
            self.data_path / f"{pair_filename}-{timeframe}.parquet",
            self.data_path / f"{pair_filename}-{timeframe}.csv",
        ]
        df = None
        for path in possible_paths:
            if path.exists():
                logger.info(f"Loading data from {path}")
                if path.suffix == ".feather": df = pd.read_feather(path)
                elif path.suffix == ".parquet": df = pd.read_parquet(path)
                else: df = pd.read_csv(path)
                break
        if df is None: raise FileNotFoundError(f"No data found for {pair} {timeframe}")
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
        elif not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df

    def create_windows(self, df: pd.DataFrame, train_days: int = 90, test_days: int = 30, step_days: int = 30):
        windows = []
        if len(df) > 0:
            time_diff = df.index[-1] - df.index[0]
            days_total = time_diff.days + time_diff.seconds / (24 * 3600)
            candles_per_day = len(df) / max(1, days_total)
        else: candles_per_day = 288
        train_candles = int(train_days * candles_per_day)
        test_candles = int(test_days * candles_per_day)
        step_candles = int(step_days * candles_per_day)
        start_idx = 0
        while start_idx + train_candles + test_candles <= len(df):
            windows.append((df.iloc[start_idx:start_idx+train_candles].copy(), df.iloc[start_idx+train_candles:start_idx+train_candles+test_candles].copy()))
            start_idx += step_candles
        return windows

    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series, model_type: str = "lightgbm"):
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        y_train_encoded = le.fit_transform(y_train)
        if model_type == "lightgbm" and LGB_AVAILABLE:
            model = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=-1, force_col_wise=True, is_unbalance=True)
        else:
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train_encoded)
        return model, le

    def simulate_trading(self, test_df: pd.DataFrame, features: pd.DataFrame, model: Any, le: Any, threshold: float, fee: float = 0.001):
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(features)
            if 1 in le.classes_:
                l_idx = np.where(le.classes_ == 1)[0][0]
                y_pred_proba = probs[:, l_idx]
            else: y_pred_proba = np.zeros(len(features))
            trade_signals = (y_pred_proba > threshold).astype(int)
        else:
            y_pred = le.inverse_transform(model.predict(features))
            trade_signals = (y_pred == 1).astype(int)
        returns = test_df["close"].pct_change().shift(-1)
        common_idx = returns.index.intersection(features.index)
        if len(common_idx) == 0: return {"total_pnl": 0.0, "profit_factor": 0.0, "sharpe": 0.0}
        returns = returns.loc[common_idx]
        sig = pd.Series(trade_signals, index=features.index).loc[common_idx]
        entries = (sig == 1) & (sig.shift(1) == 0)
        exits = (sig == 0) & (sig.shift(1) == 1)
        strat_ret = returns * sig
        strat_ret.loc[entries] -= fee
        strat_ret.loc[exits] -= fee
        strat_ret = strat_ret.dropna()
        if len(strat_ret) == 0: return {"total_pnl": 0.0, "profit_factor": 0.0, "sharpe": 0.0}
        total_pnl = (1 + strat_ret).prod() - 1
        win_ret = strat_ret[strat_ret > 0].sum()
        loss_ret = abs(strat_ret[strat_ret < 0].sum())
        pf = win_ret / max(0.0001, loss_ret)
        return {"total_pnl": total_pnl, "profit_factor": pf, "sharpe": (strat_ret.mean() / strat_ret.std() * np.sqrt(252*288)) if strat_ret.std()>0 else 0}

    def run(self, pair: str, timeframe: str, model_type: str, threshold: float):
        df = self.load_data(pair, timeframe)
        windows = self.create_windows(df)
        self.equity_curve = [1.0]
        for i, (train_df, test_df) in enumerate(windows):
            logger.info(f"Processing Window {i+1}")
            fe = FeatureEngineer(self.feature_config)
            X_train = fe.fit_transform(train_df)
            X_test = fe.transform(test_df)
            y_train_full = self.labeler.label(train_df)
            y_test_full = self.labeler.label(test_df)
            t_idx = X_train.index.intersection(y_train_full.index)
            v_idx = X_test.index.intersection(y_test_full.index)
            X_train, y_train = X_train.loc[t_idx], y_train_full.loc[t_idx]
            X_test, y_test = X_test.loc[v_idx], y_test_full.loc[v_idx]
            X_train, y_train = X_train[y_train.notna()], y_train[y_train.notna()]
            X_test, y_test = X_test[y_test.notna()], y_test[y_test.notna()]
            if len(X_train) < 100: continue
            model, le = self.train_model(X_train, y_train, model_type)
            res = self.simulate_trading(test_df.loc[X_test.index], X_test, model, le, threshold)
            self.window_results.append(res)
            self.equity_curve.append(self.equity_curve[-1] * (1 + res["total_pnl"]))
        return {"pnl": self.equity_curve[-1]-1, "pf": np.mean([r["profit_factor"] for r in self.window_results])}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--threshold", type=float, default=0.7)
    args = parser.parse_args()
    wfa = WalkForwardAnalysis()
    results = wfa.run(args.pair, args.timeframe, "lightgbm", args.threshold)
    print(f"Result: PnL={results['pnl']:.2%}, PF={results['pf']:.2f}")

if __name__ == "__main__":
    main()
