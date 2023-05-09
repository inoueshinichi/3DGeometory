"""アフィン
@ note アフィン
ホモグラフィに制約を追加したもの.
並進, 回転, スケール, スキューの4つが特徴.
2Dアフィンと3Dアフィンの2種類が主要.

@note ホモグラフィは台形へ変形させることができるが, 
アフィンは長方形を平行四辺形に変形させることしかできない. 

@note点群の扱い方. 
点(同次座標)の集合は, [DxN]の配列になる. データは列.

@note 2Dアフィン行列H(3x3)
スケール不定性(h9で3x3のH全体を正規化しても同じ変換を示す)をもつ
2Dホモグラフィ行列Hは, 8自由度を持つ.
2Dアフィンは, 更にh7=h8=0の制約があるため, -2自由度.
結果, 8-2=6自由度の3x3行列となる.

m' = [x',y',w']^T
m  = [x,y,w]
H = [
    [h1, h2, h3],
    [h4, h5, h6],
    [h7=0, h8=0, h9]]
6自由度.
アフィン変換 m' = Hm


@note 2Dアフィン行列H(3x3)の推定方法
1. 正規化(平均0,分散1)3点アルゴリズム : 6自由度に対して対応点1つで2つの方程式が利用できる.(ノイズは含まれる)
2. 下記アルゴリズム by ref `Multi View Geometry in Computer Vision` p.130

@note 2Dアフィン行列Hを求めるアルゴリズム
m' = [x',y']^T (w=1)
m  = [x ,y]^T  (w=1)
Z' = [m'_1, m'_2, m'_3, ...] (2,N)
Z  = [m_1, m_2, m_3, ...]    (2,N)

A = [Z'^T, Z^T] (N,4)

特異値分解(SVD)
A = U @ Σ V^T
U   : (N,N) 直行行列
Σ   : (N,N) 対角行列
V^T : (N,4) 直行行列

tmp = V^T[:-1]^T (4,N-1)
B = tmp[:2,:] (2,N-1)
C = tmp[2:,:] (2,N-1)
* = CB^1 (2,2)

H = [
    [*[0,0], *[0,1], 0]
    [*[1,0], *[1,1], 0]
    [     0,      0, 1]]
(3,3)


@note 3Dアフィン行列H(4x4)
スケール不定性(h16で4x4のH全体を正規化しても同じ変換を示す)をもつ
3Dホモグラフィ行列Hは, 15自由度を持つ.
2Dアフィンは, 更にh13=h14=h15=0の制約があるため, -3自由度.
結果, 15-3=12自由度の4x4行列となる.

M' = [x',y',z',w']^T
M  = [x, y, z, w]^T
H = [
    [h1, h2, h3, h4],
    [h5, h6, h7, h8],
    [h9, h10,h11,h12],
    [h13=0,h14=0,h15=0,h16]]
12自由度
射影変換 M'=HM

@note 3Dアフィン行列H(4x4)の推定方法
1. 正規化(平均0,分散1)4点アルゴリズム : 12自由度に対して対応点1つで3つの方程式が利用できる.(ノイズは含まれる)
2. 下記アルゴリズム by ref `Multi View Geometry in Computer Vision` p.130

M' = [x',y',z']^T (w=1)
M  = [x ,y,z]^T  (w=1)
Z' = [m'_1, m'_2, m'_3, ...] (3,N)
Z  = [m_1, m_2, m_3, ...]    (3,N)

A = [Z'^T, Z^T] (N,6)

特異値分解(SVD)
A = U @ Σ V^T
U   : (N,N) 直行行列
Σ   : (N,N) 対角行列
V^T : (N,6) 直行行列

tmp = V^T[:-1]^T (6,N-1)
B = tmp[:2,:] (3,N-1)
C = tmp[2:,:] (3,N-1)
* = CB^1 (3,3)

H = [
    [*[0,0], *[0,1], *[0,2], 0]
    [*[1,0], *[1,1], *[1,2], 0]
    [     0,      0,      0, 1]]
(4,4)

"""

import os
import sys
import math

import numpy as np
import scipy as sp
from scipy import ndimage

import rotation
import rvec
import quartanion
import euler

from geometry_context import GeometryContext
from euler_state import EulerState

from type_hint import *

from ransac import Ransac, RansacModel
from Homography.homography import homo_squared_errors


def find_affine3D(planar1_3d_pts: np.ndarray,
                  planar2_3d_pts: np.ndarray,
                  eps: float = 1e-9) -> np.ndarray:
    """3Dアフィン行列H (4つの対応点が必要)
    同次座標系(x,y,z,w)

    Args:
        planar1_3d_pts (np.ndarray): 第一共面の3D点群[4xN]
        planar2_2d_pts (np.ndarray): 第二共面の2D点群[4xN]
        esp (float, optional): ゼロ割防止小数. Defaults to 1e-9.

    Returns:
        np.ndarray: 3Dアフィン行列H[4x4]
    """

    if planar1_3d_pts.shape != planar2_3d_pts.shape:
        raise ValueError("Not match number of points between planar1_pts and planar2_pts. \
                         Given is planar1_3d_pts.shape: {planar1_3d_pts.shape}, \
                         planar2_pts.shape: {planar2_3d_pts_shape}")
    
    if planar1_3d_pts.shape[1] != 4:
        raise ValueError(f"Number of points planar1_3d_pts and planar2_3d_pts must be == 4. Given is {planar1_3d_pts.shape[1]}")

    ''' 点群の標準化 (数値計算上重要) '''
    # planar1
    m1 = np.mean(planar1_3d_pts[:3], axis=1) # [3x1] (mean_x, mean_y, mean_z)
    std1 = np.std(planar1_3d_pts[:3], axis=1) # [3x1] (std_x, std_y, std_z)
    max_std1 = math.max(std1[0], std1[1], std1[2]) + eps # max(std_x, std_y)
    C1 = np.diag([1.0 / max_std1, 1.0 / max_std1, 1.0 / max_std1, 1.0]) # 対角行列 [4x4]
    C1[0,2] = -m1[0] / max_std1
    C1[1,2] = -m1[1] / max_std1
    C1[2,2] = -m1[2] / max_std1
    planar1_3d_pts = C1 @ planar1_3d_pts # 標準化

    # planar2
    m2 = np.mean(planar2_3d_pts[:3], axis=1)
    std2 = np.std(planar2_3d_pts[:3], axis=1)
    max_std2 = math.max(std2[0], std2[1], std2[2]) + eps
    C2 = np.diag([1.0 / max_std2, 1.0 / max_std2, 1.0 / max_std2, 1.0])
    C2[0,2] = -m2[0] / max_std2
    C2[1,2] = -m2[1] / max_std2
    C2[2,2] = -m2[2] / max_std2
    planar2_3d_pts = C2 @ planar2_3d_pts # 標準化

    # 平均0, 分散1
    A = np.concatenate((planar1_3d_pts[:3], planar2_3d_pts[:3]), axis=0) # (3,4)
    U,S,V = np.linalg.svd(A.T)

    # Hartley-Zisserman(第2版)p.130に基づき行列B,Cを求める
    tmp = V[:3].T
    B = tmp[:3] # (3,3)
    C = tmp[3:6] # (3,3)
    tmp2 = np.concatenate((C @ np.linalg.pinv(B), np.zeros((3,1))), axis=1)
    H = np.vstack((tmp2, [0,0,0,1]))

    # 調整を元に戻す
    H = np.linalg.inv(C2) @ H @ C1
    
    return H / H[3,3]


def get_4pts_indice_of_rectangle_planar_pts(rectangle_planar_3d_objs: np.ndarray) -> Tuple[int, int, int, int]:
    """3D上の長方形共面オブジェクトの点群から
    各隅となるp1,p2,p3,p4(左上を始点として時計回り)のインデックスを求める

    Args:
        rectangle_planar_3d_objs (np.ndarray): 長方形共面オブジェクトの点群 [4xN]

    Returns:
        Tuple[int, int, int, int]: p1,p2,p3,p4に対応する4つのインデックス
    """
    pass


def embed_3d_planar(embed_planar_3d_pts: np.ndarray,
                    target_planar_3d_pts: np.ndarray) -> np.ndarray:
    """3Dアフィン変換による長方形の共面オブジェクト(同一平面上にある点群)の3D点上への埋め込み
    同次座標系(x,y,z,w)

    Args:
        embed_planar_3d_objs (np.ndarray): 共面オブジェクト(同一平面上にある点群) [4xN]
        target_planar_3d_pts (np.ndarray): 埋め込み先3D内の4点(t1,t2,t3,t4) [4x4] t* = [x,y,z,w]^T

    Returns:
        np.ndarray: 埋め込み共面オブジェクト [4xN]
    """

    if embed_planar_3d_pts.shape != target_planar_3d_pts.shape:
        raise ValueError(f"Not match shape. Given embed_rectangle_planar_3d_pts: {embed_planar_3d_pts.shape}, target_planar_3d_pts: {target_planar_3d_pts.shape}")
    
    ''' 共面オブジェクトから4点p1,p2,p3,p4(左上を始点として時計回り)を求める '''
    idx_p1, idx_p2, idx_p3, idx_p4 = get_4pts_indice_of_rectangle_planar_pts(embed_planar_3d_pts)

    # 同次座標(x,y,z,w)
    p1 = embed_planar_3d_pts[:,idx_p1] # (4,1)
    p2 = embed_planar_3d_pts[:,idx_p2] # (4,1)
    p3 = embed_planar_3d_pts[:,idx_p3] # (4,1)
    p4 = embed_planar_3d_pts[:,idx_p4] # (4,1)

    planar1_3d_pts = np.hstack((p1,p2,p3,p4)) # (4,4)

    # 3Dアフィン行列Hを推定
    H = find_affine3D(planar1_3d_pts, target_planar_3d_pts)

    # 共面オブジェクト(点群)の3Dアフィン変換
    transformed_embed_planar3d_pts = H @ embed_planar_3d_pts

    # w=1に正規化
    transformed_embed_planar3d_pts /= transformed_embed_planar3d_pts[:-1,:]

    return transformed_embed_planar3d_pts


def find_affine2D(planar1_pts: np.ndarray,
                  planar2_pts: np.ndarray,
                  eps: float = 1e-9) -> np.ndarray:
    """2Dアフィン行列H (3つの対応点が必要)
    同次座標系(x,y,w)

    Args:
        planar1_pts (np.ndarray): 第一平面の2D点群[3xN]
        planar2_pts (np.ndarray): 第二平面の2D点群[3xN]
        eps (float, optional): ゼロ割防止小数. Defaults to 1e-9.

    Returns:
        np.ndarray: 2Dアフィン行列H[3x3]
    """

    if planar1_pts.shape != planar2_pts.shape:
        raise ValueError("Not match number of points between planar1_pts and planar2_pts. \
                         Given is planar1_pts.shape: {planar1_pts.shape}, \
                         planar2_pts.shape: {planar2_pts_shape}")
    
    if planar1_pts.shape[1] != 3:
        raise ValueError(f"Number of points planar1_pts and planar2_pts must be == 3. Given is {planar1_pts.shape[1]}")

    ''' 点群の標準化 (数値計算上重要) '''
    # planar1
    m1 = np.mean(planar1_pts[:2], axis=1) # [2x1] (mean_x, mean_y)
    std1 = np.std(planar1_pts[:2], axis=1) # [2x1] (std_x, std_y)
    max_std1 = math.max(std1[0], std1[1]) + eps # max(std_x, std_y)
    C1 = np.diag([1.0 / max_std1, 1.0 / max_std1, 1.0]) # 対角行列 [3x3]
    C1[0,2] = -m1[0] / max_std1
    C1[1,2] = -m1[1] / max_std1
    planar1_pts = C1 @ planar1_pts # 標準化

    # planar2
    m2 = np.mean(planar2_pts[:2], axis=1)
    std2 = np.std(planar2_pts[:2], axis=1)
    max_std2 = math.max(std2[0], std2[1]) + eps
    C2 = np.diag([1.0 / max_std2, 1.0 / max_std2, 1.0])
    C2[0,2] = -m2[0] / max_std2
    C2[1,2] = -m2[1] / max_std2
    planar2_pts = C2 @ planar2_pts # 標準化

    # 平均が0になるように調整する. 平行移動はなくなる.
    A = np.concatenate((planar1_pts[:2], planar2_pts[:2]), axis=0)
    U,S,V = np.linalg.svd(A.T)

    # Hartley-Zisserman(第2版)p.130に基づき行列B,Cを求める
    tmp = V[:2].T
    B = tmp[:2]
    C = tmp[2:4]
    tmp2 = np.concatenate((C @ np.linalg.pinv(B), np.zeros((2,1))), axis=1)
    H = np.vstack((tmp2, [0,0,1]))

    # 調整を元に戻す
    H = np.linalg.inv(C2) @ H @ C1

    return H / H[2,2]


def alpha_for_triangle2D(planar_pts: np.ndarray, H: int, W: int) -> np.ndarray:
    """正規化された同次座標系のplanar_ptsをもつ三角形について,
    サイズ(H,W)の透明度マップを作成する.

    Args:
        planar_pts (np.ndarray): _description_
        H (int): 画像高さ
        W (int): 画像幅

    Returns:
        np.ndarray: 透明度マップ (H,W)
    """

    alpha = np.zeros((H,W), dtype=np.float32)
    for i in range(np.min(planar_pts[0,:]), np.max(planar_pts[0,:])): # min_x, max_x
        for j in range(np.min(planar_pts[1,:]), np.max(planar_pts[1,:])): # min_y, max_y
            x = np.linalg.solve(planar_pts, [i,j,1])
            if min(x) > 0: # すべての係数が正の数
                alpha[i,j] = 1
    return alpha


def embed_image_in_image(embed_img: np.ndarray,
                         target_img: np.ndarray,
                         target_pts: np.ndarray) -> np.ndarrray:
    """2Dアフィン変換による画像埋め込み
    矩形画像は2つの三角形に分割して, それぞれで2Dアフィン変換.
    同次座標系(x,y,w)

    Args:
        embed_img (np.ndarray): 埋め込み画像 Mono or RGB (H,W,C)
        target_img (np.ndarray): 埋め込み先画像 Mono or RGB (H,W,C)
        target_pts (np.ndarray): 埋め込み先画像内の4点 [3x4]

    Returns:
        np.ndarrray: 埋め込み済み画像 Mono or RGB (H,W,C)
    """

    if embed_img.shape != target_img.shape:
        raise ValueError(f"Not match shape. Given embed_img: {embed_img.shape}, target_img: {target_img.shape}")

    eH = embed_img.shape[0]
    eW = embed_img.shape[1]
    tH = target_img.shape[0]
    tW = target_img.shape[1]

    # embed_imgに含まれる`0`要素に+1する
    zero_mask = embed_img[embed_img == 0]
    copy_embed_img = np.copy(embed_img)
    copy_embed_img[zero_mask] = 1 # 視覚的に黒と認識する小数を加算

    planar1_pts = np.array([
        [0,0,1], # top-left
        [eW,0,1], # top-right
        [eW,eH,1], # bottom-right
        [0,eH,1]  # bottom-left
    ], dtype=np.float32).T # [3x4]

    # 第1三角形の3点(右上)
    planar1_tri1_pts = planar1_pts[:, [0,1,2]]
    planar2_tri1_pts = target_pts[:, [0,1,2]]

    # 2Dアフィン行列A1を推定
    H1 = find_affine2D(planar1_tri1_pts, planar2_tri1_pts)

    # 2Dアフィン変換 with A1
    img1_rt_t = ndimage.affine_transform(copy_embed_img, H1[:2,:2], (H1[0,2],H1[1,2]), (tH,tW))

    # 第1三角形の透明度マップ
    alpha1 = alpha_for_triangle2D(planar2_tri1_pts, tH, tW)

    img3 = (1-alpha1)*target_img + alpha1*img1_rt_t

    # 第2の三角形の3点(左下)
    planar1_tri2_pts = planar1_pts[:, [2,3,0]]
    planar2_tri2_pts = target_pts[:, [2,3,0]]

    # 2Dアフィン行列A2を推定
    H2 = find_affine2D(planar1_tri2_pts, planar2_tri2_pts)

    # 2Dアフィン with A2
    img1_lt_t = ndimage.affine_transform(copy_embed_img, H2[:2,:2], (H2[0,2],H2[1,2]), (tH,tW))

    # 第2三角形の透明度マップ
    alpha2 = alpha_for_triangle2D(planar2_tri2_pts, tH, tW)

    img4 = (1-alpha2)*img3 + alpha2*img1_lt_t

    return img4


def embed_image_in_image_with_devide_affine_warping(
        embed_img: np.ndarray,
        target_img: np.ndarray,
        target_pts: np.ndarray,
        patches: Tuple[int, int]) -> np.ndarray:
    """2D分割アフィンワーピングによる画像埋め込み
    同次座標系(x,y,w)

    Args:
        embed_img (np.ndarray): 埋め込み画像 Mono or RGB (H,W,C)
        target_img (np.ndarray): 埋め込み先画像 Mono or RGB (H,W,C)
        target_pts (np.ndarray): 埋め込み先画像内の制御点 [3xN] Nは偶数
        patchs (Tuple[int, int]): 縦横のパッチ数(縦,横) N = 縦 * 横

    Returns:
        np.ndarray: 埋め込み済み画像 Mono or RGB (H,W,C)
    """

    color_flag: bool = len(target_img.shape) == 3

    if embed_img.shape != target_img.shape:
        raise ValueError(f"Not match shape. Given embed_img: {embed_img.shape}, target_img: {target_img.shape}")

    N = target_pts.shape[1]
    if N % 2 != 0:
        raise ValueError(f"Number of target_points must be even. Given is {N}")
    
    rows, cols = patches

    if rows * cols != N:
        raise ValueError(f"Must rows * cols = {N}. Given is (rows,cols)={patches}")
    
    eH = embed_img.shape[0]
    eW = embed_img.shape[1]

    ePatchH = eH / rows
    ePatchW = eW / cols
    ePatchSize = (ePatchH, ePatchW)

    if ePatchH % 2 != 0 or ePatchW %2 != 0:
        raise ValueError(f"Patch size must be even number. Given is {ePatchSize}")
    
    # 変形先画像
    transform_img = np.zeros(target_img.shape, dtype=np.uint8)
    
    # 出力画像
    result_img = target_img.copy()

    # 埋め込み画像の制御点を作成 (x,y,w=1)
    embed_control_pts = np.zeros((rows+1, cols+1, 3), dtype=np.float32)
    for i in range(0, rows+1):
        for j in range(0, cols+1):

            # y座標
            if i == 0:
                y = 0
            else:
                y = i * ePatchH - 1

            # x座標
            if j == 0:
                x = 0
            else:
                x = j * ePatchW - 1

            embed_control_pts[i,j,:] = np.array([x,y,1], dtype=np.float32)

    # 埋め込み画像の制御点からドロネー三角形分割法によって, 各三角形のインデックスを取得
    # https://note.nkmk.me/python-scipy-matplotlib-delaunay-voronoi/
    embed_control_pts = embed_control_pts.reshape(-1, 3) # (N,3) 
    triangles = sp.spacial.Delaunay(embed_control_pts)
    tri_indices = triangles.simplices # (N,3) (idx_p1,idx_p2,idx_p3)

    # 各三角形毎にアフィン変換による画像埋め込みを行う
    embed_control_pts = embed_control_pts.T # (3,N)
    for indice in tri_indices:
        # 制御点とターゲット点の対応点から三角形を構成する点を3つ選んで, アフィン行列Hを求める
        H = find_affine2D(embed_control_pts[:,indice], target_pts[:,indice]) # (x,y,w) - (x',y',z')

        # アフィン変換
        if color_flag:
            for c in range(embed_img.shape[2]):
                transform_img[:,:,c] = ndimage.affine_transform(
                    embed_img[:,:,c], H[:2,:2], (H[0,2],H[1,2]), target_img.shape[:2])
        else:
            transform_img = ndimage.affine_transform(
                embed_img, H[:2,:2], (H[0,2],H[1,2]), target_img.shape[:2])
        
        # 三角形の透明度マップ
        alpha = alpha_for_triangle2D(embed_control_pts[:,indice].astype(np.int32), target_img.shape[0], target_img.shape[1])

        # 三角形を画像に追加する
        result_img[alpha>0] = transform_img[alpha>0]

    return result_img






