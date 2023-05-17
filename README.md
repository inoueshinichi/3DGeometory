# 3DCV

### 参考
+ かみのメモ https://kamino.hatenablog.com/archive
+ 実践コンピュータビジョン 

### 座標系設定
1. 同次座標系 (sx,sy,sz,sw)=(x/w,y/w,z/w,1)
2. 左手座標系と右手座標系  
3. Zup, Yup  
4. Xforward, Yforward, Zforward
5. クロス積の結果 (数式は同じだが, 座標系設定で定義が異なる.)
6. 座標系設定の変換

### 3D 基本モジュール
1. 回転行列(3x3)
2. 回転ベクトル(3x1)
3. クォータニオン(4x1)
4. オイラー角(Θ1, Θ2, Θ3)
5. 座標系のPose行列M=(R'|t') (4x4)
6. フレーム定義 M_new_frame = AddFrame(M_frame, M_plus) : M = (R'|t')
7. 座標変換 T_new_coordinate = Transform(T_coordinate, T_plus) T = (R|t)
8. フレーム定義 <-> 座標変換 T = (R|t) = (R=R'^T|t=-R'^T*t')
9. 回転行列(3x3) <-> 回転ベクトル(3x1)
10. 回転行列(3x3) <-> クォータニオン(4x1)
11. 回転行列(3x3) <-> オイラー角(Θ1, Θ2, Θ3)
12. クォータニオン(4x1) <-> 回転行列(3x1)

### カメラモジュール
1. カメラのView行列 V=(R|t) (4x4)
2. LookAtによるカメラのView行列の作成
3. View行列からカメラ座標のPoseを取得
4. カメラ座標系から正規化座標系\[-1,+1\]への変換 NIPC x = Xc/Zc, y = Yc/Zc. Mc = (V @ Mw), m = Mc/Zc : Mw=\[Xw,Yw,Zw,1\], Mc=\[Xc,Yc,Zc,1\], m=\[x,y,s=w=Zc\] = \[x/s,y/s,1/] = \[x,y\]
5. キャリブレーション行列K (3x3)
6. カメラ行列P = KV =  K(R|t) = (KR|Kt) (3x4)
7. カメラ行列Pの分解(RQ) P = (KR|Kt) = (P\[:3,:3]|P\[3,:3\]) -(SVD)-> R = UW^TV^T,  UWV^T, t = U\[:,3\], -\U\[:,3\]. -> 4つの解(UW^TV^T|U\[:,3]), (UW^TV^T|-U\[:,3\]), (UWV^T|U\[:,3]), (UW^T|-U\[:,3\]).

### ホモグラフィ
+ ホモグラフィはスケール不定性を持つ
1. 2Dホモグラフィ行列(3x3)
2. 3Dホモグラフィ行列(4x4)
3. 2Dアフィン行列(3x3) : h7=h8=0
4. 3Dアフィン行列(3x3) : h13=h14=h15=0
5. 2Dリジッド行列(3x3) : 2Dアフィン行列かつスケール=1(=Sx=Sy)
6. 3Dリジッド行列(4x4) : 3Dアフィン行列かつスケール=1(=Sx=Sy=Sz)

### エピポーラ幾何
1. 基礎行列F (3x3) rank(F) = 2, 射影行列
2. 基本行列E (3x3) rank(E) = 2, 0でない2つの特異値は等しい, 射影行列.
6. 基本行列Eの分解 E = \[1_t_2|x\] @ 1_R_2
7. エピポーラ線l1とl2, エピ極e1とe2, エピ極はF, Eのカーネル : Fe1=0, e2^TF=F^Te2=0, Ee1=0, e2^TE=0, E^Te2=0. 
8. 三角測量

### キャリブレーション
1. Zhang calib (3D-2D)
2. Self calib (特徴点検出->対応点作成->基礎行列Fの推定->カメラ行列Pの計算. Additional, キャリブレーション行列Kが判明していれば, -> 基本行列Eの計算 -> 1_R_2, 1_t_2に分解. カメラ座標系c1とc2のPoseを計算)
3. PnP calib (3D-2D リフレクション) キャリブレーション行列Kが必須.

### Stereo
1. 平行化(Refine)

### SfM(Structure from Motion)
1. 



