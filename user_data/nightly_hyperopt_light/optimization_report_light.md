# Light Overnight Hyperparameter Optimization Report

**Date:** 2025-12-26 03:51:30

## Summary

- **Best Sharpe Ratio:** 1.3946
- **Total Trials:** 500
- **Optimization Duration:** 3.87 hours

## Best Parameters

```json
{
  "max_depth": 5,
  "learning_rate": 0.027356839486920186,
  "n_estimators": 787,
  "subsample": 0.8262022674003212,
  "colsample_bytree": 0.6125974089402942,
  "gamma": 1.4512299061085965,
  "reg_alpha": 0.09078757042158325,
  "reg_lambda": 0.7182835076662109,
  "min_child_weight": 1
}
```

## Comparison with Previous Best (3-Year Model)

| Parameter | Previous Best | Light Best | Change |
|-----------|---------------|------------|--------|
| colsample_bytree | 0.6504 | 0.6126 | -5.8% |
| gamma | 2.1019 | 1.4512 | -31.0% |
| learning_rate | 0.0367 | 0.0274 | -25.5% |
| max_depth | 5 | 5 | - |
| min_child_weight | N/A | 1 | - |
| n_estimators | 718 | 787 | - |
| reg_alpha | N/A | 0.09078757042158325 | - |
| reg_lambda | N/A | 0.7182835076662109 | - |
| subsample | 0.6077 | 0.8262 | +36.0% |

## Resource Usage

- **Peak Memory Usage:** 14.2 GB (90.9%)
- **Disk Free:** 41.4 GB
- **CPU Usage:** 0.2%
- **Elapsed Time:** 3.87 hours

## Recommendations

1. **Model Deployment:** Consider deploying the new parameters if Sharpe Ratio improvement > 5%
2. **Next Optimization:** Schedule next run in 3-7 days
3. **Data Freshness:** Ensure data is updated before next optimization
4. **Monitoring:** Monitor model performance after deployment
