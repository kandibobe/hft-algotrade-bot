"""
Hierarchical Risk Parity (HRP) Optimization
===========================================

Implementation of Marcos Lopez de Prado's HRP algorithm.
Used for dynamic portfolio allocation.
"""


import numpy as np
import pandas as pd
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform


def getIVP(cov, **kargs):
    """Compute the inverse variance portfolio."""
    ivp = 1.0 / np.diag(cov)
    ivp /= ivp.sum()
    return ivp


def getClusterVar(cov, cItems):
    """Compute cluster variance."""
    cov_ = cov.loc[cItems, cItems]  # matrix slice
    w_ = getIVP(cov_).reshape(-1, 1)
    cVar = np.dot(np.dot(w_.T, cov_), w_)[0, 0]
    return cVar


def getQuasiDiag(link):
    """Sort clustered items by distance."""
    link = link.astype(int)
    sortIx = pd.Series([link[-1, 0], link[-1, 1]])
    numItems = link[-1, 3]  # number of original items
    while sortIx.max() >= numItems:
        sortIx.index = range(0, sortIx.shape[0] * 2, 2)  # make space
        df0 = sortIx[sortIx >= numItems]  # find clusters
        i = df0.index
        j = df0.values - numItems
        sortIx[i] = link[j, 0]  # item 1
        df0 = pd.Series(link[j, 1], index=i + 1)
        sortIx = pd.concat([sortIx, df0])  # reorder
        sortIx = sortIx.sort_index()  # reindex
        sortIx.index = range(sortIx.shape[0])  # reindex
    return sortIx.tolist()


def getRecBipart(cov, sortIx):
    """Compute HRP allocation recursively."""
    w = pd.Series(1, index=sortIx)
    cItems = [sortIx]  # initialize all items in one cluster
    while len(cItems) > 0:
        cItems = [
            i[j:k]
            for i in cItems
            for j, k in ((0, len(i) // 2), (len(i) // 2, len(i)))
            if len(i) > 1
        ]  # bi-section
        for i in range(0, len(cItems), 2):  # parse in pairs
            cItems0 = cItems[i]  # cluster 1
            cItems1 = cItems[i + 1]  # cluster 2
            cVar0 = getClusterVar(cov, cItems0)
            cVar1 = getClusterVar(cov, cItems1)
            alpha = 1 - cVar0 / (cVar0 + cVar1)
            w[cItems0] *= alpha  # weight 1
            w[cItems1] *= 1 - alpha  # weight 2
    return w


def get_hrp_weights(prices: pd.DataFrame) -> dict[str, float]:
    """
    Calculate HRP weights for a given dataframe of prices.

    Args:
        prices: DataFrame where columns are assets and rows are timestamps.

    Returns:
        Dictionary {asset: weight}
    """
    # 1. Calculate returns
    returns = prices.pct_change().dropna()

    if len(returns) < 10 or len(returns.columns) < 2:
        # Fallback to equal weights
        n = len(prices.columns)
        return dict.fromkeys(prices.columns, 1.0 / n)

    # 2. Covariance and Correlation
    cov = returns.cov()
    corr = returns.corr()

    # 3. Clustering
    dist = correlation_to_distance(corr)
    link = sch.linkage(dist, "single")

    # 4. Sorting
    sortIx = getQuasiDiag(link)
    sortIx = corr.index[sortIx].tolist()

    # 5. Allocation
    weights = getRecBipart(cov, sortIx)

    return weights.to_dict()


def correlation_to_distance(corr):
    """Convert correlation matrix to distance matrix."""
    dist = ((1 - corr) / 2.0) ** 0.5  # distance matrix
    return squareform(dist)  # convert to vector for linkage
