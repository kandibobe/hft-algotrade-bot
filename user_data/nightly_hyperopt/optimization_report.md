# Nightly Hyperparameter Optimization Report

**Date:** 2026-01-11 19:34:46

## Summary

- **Best Sharpe Ratio:** 4.1945
- **Total Trials:** 608
- **Optimization Duration:** 4.06 hours

## Best Parameters

```json
{
  "max_depth": 4,
  "learning_rate": 0.005126375199465651,
  "n_estimators": 763,
  "subsample": 0.7292663007483098,
  "colsample_bytree": 0.6574842528586048,
  "gamma": 1.0831135115645678,
  "reg_alpha": 0.41593433690248016,
  "reg_lambda": 0.8580240992542637,
  "min_child_weight": 6
}
```

## Comparison with Previous Best (3-Year Model)

| Parameter | Previous Best | Nightly Best | Change |
|-----------|---------------|--------------|--------|
| colsample_bytree | 0.6504 | 0.6575 | +1.1% |
| gamma | 2.1019 | 1.0831 | -48.5% |
| learning_rate | 0.0367 | 0.0051 | -86.0% |
| max_depth | 5 | 4 | - |
| min_child_weight | N/A | 6 | - |
| n_estimators | 718 | 763 | - |
| reg_alpha | N/A | 0.41593433690248016 | - |
| reg_lambda | N/A | 0.8580240992542637 | - |
| subsample | 0.6077 | 0.7293 | +20.0% |

## Resource Usage

- **Peak Memory Usage:** 12.1 GB (77.6%)
- **Disk Free:** 129.5 GB
- **CPU Usage:** 4.6%
- **Elapsed Time:** 4.06 hours

## Recommendations

1. **Model Deployment:** Consider deploying the new parameters if Sharpe Ratio improvement > 5%
2. **Next Optimization:** Schedule next run in 3-7 days
3. **Data Freshness:** Ensure data is updated before next optimization
4. **Monitoring:** Monitor model performance after deployment
