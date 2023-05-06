# 3DCV

### 参考
+ かみのメモ https://kamino.hatenablog.com/archive
+ 実践コンピュータビジョン 

### 3D 基本モジュール
1. 回転行列(3x3)
2. 回転ベクトル(3x1)
3. クォータニオン(4x1)
4. オイラー角(Θ1, Θ2, Θ3)
5. 座標系のPose行列M=(R|t) (4x4)
6. フレーム変換(定義) M_new_frame = AddFrame(M_frame, M_plus)
7. 座標変換 T_new_coordinate = Transform(T_coordinate, T_plus) 
8. フレーム変換 <-> 座標変換 T = (R'|t') = (R'=R^T|t'=-R^T*t) : M = (R|t)
9. カメラのView行列V=(R'|t') (4x4)
10. LookAtによるカメラのView行列の作成
11. View行列からカメラ座標のPoseを取得
12. 回転行列(3x3) <-> 回転ベクトル(3x1)
13. 回転行列(3x3) <-> クォータニオン(4x1)
14. 回転行列(3x3) <-> オイラー角(Θ1, Θ2, Θ3)
15. クォータニオン(4x1) <-> 回転行列(3x1)

### 3D 多視点幾何モジュール


### 座標軸の設定
1. 左手座標系と右手座標系  
2. Zup, Yup  
3. Xforward, Yforward, Zforward
4. クロス積の結果 (数式は同じだが, 座標系設定で定義が異なる.)
