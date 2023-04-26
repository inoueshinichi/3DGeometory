"""基礎行列Fの推定

@note 基礎行列FのDLT法による同次連立方程式(正規化8点アルゴリズム)
@warning 平面シーンで破錠してしまうので注意.

@note 対応点
m1j = [x1j,y1j,w1j]^T
m2j = [x2j,y2j,w2j]^T

@note 対応点を正規化する
mean(m1j) = (mx1, my1, mw1)
mean(m2j) = (mx2, my2, mw2)
std(m1j[:2]) = スカラ with x1jとy1jをひっくるめての標準偏差
std(m2j[:2]) = スカラ with x2jとy2jをひっくるめての標準偏差

※ 画像平面の中心を(0,0)として, 各点の距離の標準偏差が√2になるように正規化する
m1j_normalized = √2 * (m1j - mean(m1j)) / std(m1j[:2]])
m2j_normalized = √2 * (m2j - mean(m2j)) / std(m2j[:2]))

F = [[f1,f2,f3],
     [f4,f5,f6],
     [f,7,f8,f9]]
基礎行列Fはスケールが不変なので, 8自由度になる.

エピポーラ拘束 
m1j^T*F*m2j = 0

DLTによる同次連立方程式
`Ax=0`

SVDによる最小二乗法
min |Ax| 解 -> A = UΣV^T の最小特異値に対応するV^Tの列ベクトル

※1対応点に対して1つの方程式が得られる.
x = [f1,f2,f3,f4,f5,f6,f7,f8,f9]
A = [
    [x1j*x2j, x1j*y2j, x1j*w2j, y1j*x2j, y1j*y2j, y1j*w2j, w1j*x2j, w1j*y2j, w1j*w2j] : j = 1
    :
    :
    [x1n*x2n, x1n*y2n, x1n*w2n, y1n*x2n, y1n*y2n, y1n*w2n, w1n*x2n, w1n*y2n, w1n*w2n] : j = n
]
+ RANSAC
"""

import os
import sys
import math

import numpy as np

import rotation
import rvec
import quartanion
import euler

from geometry_context import GeometryContext
from euler_state import EulerState

from type_hint import *

from ransac import Ransac, RansacModel

def sampson_error(x1: np.ndarray, x2: np.ndarray, F: np.ndarray) -> np.ndarray:
    """サンプソン誤差
    Sampson = diag(x1j^2 @ F @ x2j)^2 / (Fx1j[0])^2 + (Fx1j[1])^2 + (Fx2j[0])^2 + (Fx2j[1])^2

    Args:
        x1 (np.ndarray): 画像1上の点群 [3xN]
        x2 (np.ndarray): 画像2上の点群 [3xN]
        F (np.ndarray): 基礎行列F [3x3]

    Returns:
        np.ndarray: 各点のサンプソン誤差の配列[1xN]
    """
    Fx1 = F @ x1 # [3xN]
    Fx2 = F @ x2 # [3xN]
    denominators = Fx1[0]**2 + Fx1[1]**2 + Fx2[0]**2 + Fx2[1]**2
    numerators = (np.diag(x1.T @ F @ x2))**2

    errors = numerators / denominators # [1xN]
    return errors


def find_fundamental(img1_pts: np.ndarray, img2_pts: np.ndarray) -> np.ndarray:
    """正規化8点アルゴリズムによる基礎行列Fの推定
    2D同次座標(x,y,w) 

    Args:
        img1_pts (np.ndarray): 画像1上の点群 [3xN]
        img2_pts (np.ndarray): 画像2上の点群 [3xN]

    Returns:
        np.ndarray: 推定した基礎行列F[3x3]
    """
    if img1_pts.shape[0] != 3 or img2_pts.shape[0] != 3:
        raise ValueError(f"Not match dim3 of coordinate. Given is img1_pts: {img1_pts.shape[0]}, img2_pts: {img2_pts.shape[0]}")

    if img1_pts.shape[1] != img2_pts.shape[1]:
        raise ValueError(f"Not match datasize between img1_pts and img2_pts. Given is img1_pts: {img1_pts.shape[1]}, img2_pts: {img2_pts.shape[1]}")
    
    N: int = img1_pts.shape[1] # データサイズ

    # 画像平面1
    img1_pts /= img1_pts[-1,:] # w=1
    mean1 = np.mean(img1_pts[:2], axis=1) # (mx,my)
    S1 = np.sqrt(2) / np.std(img1_pts[:2])
    T1 = np.array([
        [S1, 0, -S1*mean1[0]],
        [0, S1, -S1*mean1[0]],
        [0, 0, 1]
        ], dtype=np.float32)
    img1_pts_normalized = T1 @ img1_pts # 正規化

    # 画像平面2
    img2_pts /= img2_pts[-1,:] # w=1
    mean2 = np.mean(img2_pts[:2], axis=1) # (mx,my)
    S2 = np.sqrt(2) / np.std(img2_pts[:2])
    T2 = np.array([
        [S2, 0, -S2*mean2[0]],
        [0, S2, -S2*mean2[0]],
        [0, 0, 1]
        ], dtype=np.float32)
    img2_pts_normalized = T2 @ img2_pts # 正規化

    # エイリアス
    x1, x2 = img1_pts_normalized, img2_pts_normalized

    # DLT法
    A = np.zeros((N, 9), dtype=np.float32)
    for i in range(0, N):
        A[i] = [x1[0,i]*x2[0,i], \
                x1[0,1]*x2[1,i], \
                x1[0,i]*x2[2,i], \
                x1[1,i]*x2[0,i], \
                x1[1,i]*x2[1,i], \
                x1[1,i]*x2[2,i], \
                x1[2,i]*x2[0,i], \
                x1[2,i]*x2[1,i], \
                x1[2,i]*x2[2,i] ] # 9列
    
    # 最小二乗法 min |Ax| SVDで解く
    U,S,V = np.linalg.svd(A)
    F = V[-1].reshape(3,3) # 最小特異値に対応する直行行列Vのベクトル

    # Fの制約 rank(F)=2, det(F)=0
    U,S,V = np.linalg.svd(F)
    S[2] = 0 # 第3成分の特異値を0にする
    F = U @ np.diag(S) @ V

    # 正規化を元に戻す
    F = T1.T @ F @ T2

    # f9=1に正規化
    return F / F[2,2]


class RansacFundamentalModel(RansacModel):

    def __init__(self):
        super(RansacFundamentalModel, self).__init__()
        pass

    def fit(self, data) -> Any:
        # 8つの対応点を使用して基礎行列Fを推定する

        # データを転置し2つの点群に分ける
        data = data.T # [6x8]
        x1 = data[:3,:] # [3x8]
        x2 = data[3:,:] # [3x8]

        # 基礎行列Fの推定
        F = find_fundamental(x1, x2)

        return F
    
    def get_error(self, data, estimated_model: Any) -> np.ndarray:
        # サンプソン距離(誤差)

        # データを転置し2つの点群に分ける
        data = data.T # [6xN]
        x1 = data[:3,:] # [3xN]
        x2 = data[3:,:] # [3xN]

        # サンプソン誤差
        return sampson_error(x1, x2, estimated_model)


def find_fundamental_with_ransac(img1_pts: np.ndarray, 
                                 img2_pts: np.ndarray,
                                 match_threashold: float = 1e-6,
                                 max_iter: int = 5000) -> np.ndarray:
    """RANSACによるロバストな基礎行列Fの推定
    2D同次座標系[x,y,w]

    Args:
        img1_pts (np.ndarray): 画像1上の点群 [3xN]
        img2_pts (np.ndarray): 画像2上の点群 [3xN]
        max_iter (int, optional): Ransacの最大反復回数. Defaults to 1000.
        match_threshold (int, optional): インライア閾値. Defaults to 3.

        インライア閾値に使用する誤差はサンプソン距離.
        Sampson = diag(x1j^2 @ F @ x2j)^2 / (Fx1j[0])^2 + (Fx1j[1])^2 + (Fx2j[0])^2 + (Fx2j[1])^2

    Returns:
        np.ndarray: ロバストな基礎行列F[3x3]
    """
    # RansacFundamental
    model = RansacFundamentalModel()
    ransac = Ransac(required_min_num_data=8, # 8点必要
                    required_inliers=20,
                    match_threshold=match_threashold,
                    max_iter=max_iter)
    
    # 対応点を1つのデータ形式として連結
    data = np.vstack((img1_pts, img2_pts)) # [6xN]
    data = data.T # 転置[Nx6]

    # Ransacによるロバストな推定モデルの取得
    robust_F, inlier_mask = ransac.execute(data=data, model=model)

    return robust_F, inlier_mask

