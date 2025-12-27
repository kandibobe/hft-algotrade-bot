# Nightly Hyperparameter Optimization Report

**Date:** 2025-12-25 23:44:47

## Summary

- **Best Sharpe Ratio:** 10.4692
- **Total Trials:** 500
- **Optimization Duration:** 0.07 hours

## Best Parameters

```json
{
  "max_depth": 5,
  "learning_rate": 0.008614583068091644,
  "n_estimators": 569,
  "subsample": 0.7146553299488577,
  "colsample_bytree": 0.73744054941768,
  "gamma": 0.4364922650451739,
  "reg_alpha": 0.3555118894830608,
  "reg_lambda": 1.994710585967554,
  "min_child_weight": 1
}
```

## Comparison with Previous Best (3-Year Model)

| Parameter | Previous Best | Nightly Best | Change |
|-----------|---------------|--------------|--------|
| colsample_bytree | 0.6504 | 0.7374 | +13.4% |
| gamma | 2.1019 | 0.4365 | -79.2% |
| learning_rate | 0.0367 | 0.0086 | -76.5% |
| max_depth | 5 | 5 | - |
| min_child_weight | N/A | 1 | - |
| n_estimators | 718 | 569 | - |
| reg_alpha | N/A | 0.3555118894830608 | - |
| reg_lambda | N/A | 1.994710585967554 | - |
| subsample | 0.6077 | 0.7147 | +17.6% |

## Resource Usage

- **Peak Memory Usage:** 13.1 GB (83.8%)
- **Disk Free:** 41.6 GB
- **CPU Usage:** 8.2%
- **Elapsed Time:** 0.07 hours

## Recommendations

1. **Model Deployment:** Consider deploying the new parameters if Sharpe Ratio improvement > 5%
2. **Next Optimization:** Schedule next run in 3-7 days
3. **Data Freshness:** Ensure data is updated before next optimization
4. **Monitoring:** Monitor model performance after deployment
