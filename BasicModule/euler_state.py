"""オイラー角
24パターン:
    i]  内因性(ローカル軸) or 外因性(ワールド軸)
    ii] 回転順序
        古典オイラー角
            XYX, XZX, YXY, YZY, ZXZ, ZYZ
        ブライアント角
            XYZ, XZY, YXZ, YZX, ZXY, ZYX

ジンバルロック発生条件:
    古典オイラー角 -> 第二軸が0,pi
    ブライアント角 -> 第二軸が±pi/2
    ※ 通常, ジンバルロック発生時は, 一意な回転状態(回転行列の状態)に対して,
      オイラー角(θ1,θ2,θ3)のθ1±θ2の組み合わせが無数に存在し, 一意な解が
      得られないが, 第三軸の角度=0とすることで, 一意な解を決めることができる.
    ※ オイラー角は回転順序の各軸で従属関係が存在し, 最初の軸の回転状態が次の軸の回転に影響を与える.
    first_axis -> second_axis -> third_axis

行列は列優先表現とする. numpyのデータ配列は行優先.

内因性と外因性の関係:
    内因性ZXY = 外因性YXZ : (R(Z)@R(X)@R(Y))
"""

'''
内因性 XYX 完
内因性 XZX 完
内因性 YXY 完
内因性 YZY 完
内因性 ZXZ 完
内因性 ZYZ 完
-
内因性 XYZ 完
内因性 XZY 完
内因性 YXZ 完
内因性 YZX 完
内因性 ZXY 完
内因性 ZYX 完
---------
外因性 XYX 完
外因性 XZX 完
外因性 YXY 完
外因性 YZY 完
外因性 ZXZ 完
外因性 ZYZ 完
-
外因性 XYZ 完
外因性 XZY 完
外因性 YXZ 完
外因性 YZX 完
外因性 ZXY 完
外因性 ZYX 完
'''

import os
import sys

module_parent_dir = '/'.join([os.path.dirname(__file__), '..'])
sys.path.append(module_parent_dir)


import math
import abc
import inspect

import numpy as np

from type_hint import *

from BasicModule.naive_rotation import ax_rot, ay_rot, az_rot
from BasicModule.utility import near_equal, near_zero


class EulerState(metaclass=abc.ABCMeta):

    # 派生クラスへのインターフェースAPIの強制
    @staticmethod
    def overrides(klass):
        def check_super(method) -> Any:
            method_name = method.__name__
            msg = f"`{method_name}()` is not defined in `{klass.__name__}`."
            assert method_name in dir(klass), msg

        def wrapper(method) -> Any:
            check_super(method)
            return method

        return wrapper

    def __init__(self, gibmal_eps: float=0.001):
        self.gimbal_eps: float = gibmal_eps

    @abc.abstractmethod
    def to_rot(self,
               theta1_rad: float, 
               theta2_rad: float, 
               theta3_rad: float) -> np.ndarray:
        
        func_name = inspect.currentframe().f_code.co_name
        class_name = self.__class__.__name__
        raise NotImplementedError(f"No implement {func_name} on {class_name}")
    
    @abc.abstractclassmethod
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
    
        func_name = inspect.currentframe().f_code.co_name
        class_name = self.__class__.__name__
        raise NotImplementedError(f"No implement {func_name} on {class_name}")


# 内因性 XYX(X1YX2)
class EulerInnerXYXState(EulerState):

    def __init__(self):
        super(EulerInnerXYXState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
    
        return ax_rot(theta1_rad) @ ay_rot(theta2_rad) @ ax_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Y軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

        [[C(Y), S(Y)S(X2), C(X2)S(Y)],
         [S(X1)S(Y), C(X1)C(X2)-C(Y)S(X1)S(X2), -C(X1)S(X2)-C(Y)C(X2)S(X1)],
         [-C(X1)S(Y), C(X2)S(X1)+C(X1)C(Y)S(X2), C(X1)C(Y)C(X2)-S(X1)S(X2)]]

            R_global = R(X1)@R(Y)@R(X2)

        Y=0のとき
        r22=cos(X1+X2), r32=sin(X1+X2) where X2=0
        Z=piのとき
        r22=cos(X1-X2), r32=sin(X1-X2) where X2=0
        Returns:
            Tuple[float, float, float]: XYX euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax1_rad, ay_rad, ax2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r11=cos(Y)の値で場合分け
        if near_zero(r11 - 1.0, eps=self.gimbal_eps):
            # r11 == +1, Y=0
            ax1_rad = math.atan2(r32, r22)
            ay_rad = 0.0
            ax2_rad = 0.0 # Y軸のジンバルロックに従属
        elif near_zero(r11 + 1.0, eps=self.gimbal_eps):
            # r11 == -1, Y=pi
            ax1_rad = math.atan2(r32, r22)
            ay_rad = math.pi
            ax2_rad = 0.0 # Y軸のジンバルロックに従属
        else:
            ax1_rad = math.atan2(r21, -r31)
            ay_rad = math.acos(r11)
            ax2_rad = math.atan2(r12, r13)
        
        # XYX Euler
        return (ax1_rad, ay_rad, ax2_rad)

# 内因性 XZX(X1ZX2)
class EulerInnerXZXState(EulerState):

    def __init__(self):
        super(EulerInnerXZXState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ax_rot(theta1_rad) @ az_rot(theta2_rad) @ ax_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Z軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(X1)@R(Z)@R(X2)

        [[C(Z), -C(X2)S(Z), S(Z)S(X2)],
         [C(X1)S(Z), C(X1)S(Z)C(X2)-S(X1)S(X2), -C(X2)S(X1)-C(X1)C(Z)S(X2)],
         [S(X1)S(Z), C(X1)S(X2)+C(Z)C(X2)S(X1), C(X1)C(X2)-C(Z)S(X1)S(X2)]]

        Z=0のとき
        r22=cos(X1+X2), r32=sin(X1+X2) where X2=0
        Z=piのとき
        r22=-cos(X1-X2), r32=-sin(X1-X2) where X2=0
        Returns:
            Tuple[float, float, float]: XZX euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax1_rad, az_rad, ax2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r11=cos(Z)の値で場合分け
        if near_zero(r11 - 1.0, eps=self.gimbal_eps):
            # r11 == +1, Z=0
            ax1_rad = math.atan2(r32, r22)
            az_rad = 0.0 
            ax2_rad = 0.0 # Z軸のジンバルロックに従属
        elif near_zero(r11 + 1.0, eps=self.gimbal_eps):
            # r11 == -1, Z=pi
            ax1_rad = math.atan2(r32, r22)
            az_rad = math.pi
            ax2_rad = 0.0 # Z軸のジンバルロックに従属
        else:
            ax1_rad = math.atan2(r31, r21)
            az_rad = math.acos(r11)
            ax2_rad = math.atan2(r13, -r12)

        # XZX euler
        return (ax1_rad, az_rad, ax2_rad)

# 内因性 YXY(Y1XY2)
class EulerInnerYXYState(EulerState):

    def __init__(self):
        super(EulerInnerYXYState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ay_rot(theta1_rad) @ ax_rot(theta2_rad) @ ay_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        X軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Y1)@R(X)@R(Y2)

        [[C(Y1)C(Y2)-C(X)S(Y1)S(Y2), S(Y1)S(X), C(Y1)S(Y2)+C(X)C(Y2)S(Y1)],
         [S(X)S(Y2), C(X), -C(Y2)S(X)],
         [-C(Y2)S(Y1)-C(Y1)C(X)S(Y2), C(Y1)S(X), C(Y1)C(X)C(Y2)-S(Y1)S(Y2)]]

        X=0のとき
        r13=sin(Y1+Y2), r33=cos(Y1+Y2) where Y2=0
        X=piのとき
        r13=-sin(Y1-Y2), r33=-cos(Y1-Y2) where Y2=0
        Returns:
            Tuple[float, float, float]: YXY euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ay1_rad, ax_rad, ay2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r22=cos(X)の値で場合分け
        if near_zero(r22 - 1.0, eps=self.gimbal_eps):
            # r22 == +1, X=0
            ay1_rad = math.atan2(r13, r33)
            ax_rad = 0.0
            ay2_rad = 0.0 # X軸のジンバルロックに従属
        elif near_zero(r22 + 1.0, eps=self.gimbal_eps):
            # r22 == -1, X=pi
            ay1_rad = math.atan2(r13, r33)
            ax_rad = math.pi
            ay2_rad = 0.0 # X軸のジンバルロックに従属
        else:
            # -1 < r22 < +1
            ay1_rad = math.atan2(r12, r32)
            ax_rad = math.acos(r22)
            ay2_rad = math.atan2(r21, -r23)

        # Euler YXY
        return (ay1_rad, ax_rad, ay2_rad)

# 内因性 YZY(Y1ZY2)
class EulerInnerYZYState(EulerState):

    def __init__(self):
        super(EulerInnerYZYState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ay_rot(theta1_rad) @ az_rot(theta2_rad) @ ay_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Z軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Y1)@R(Z)@R(Y2)

        [[C(Y1)C(Z)C(Y2)-S(Y1)S(Y2), -C(Y1)S(Z), C(Y2)S(Y1)+C(Y1)C(Z)S(Y2)],
         [C(Y2)S(Z), C(Z), S(Z)S(Y2)],
         [-C(Y1)S(Y2)-C(Z)C(Y2)S(Y1), S(Y1)S(Z), C(Y1)C(Y2)-C(Z)S(Y1)S(Y2)]]

        Z=0のとき
        r13=sin(Y1+Y2), r33=cos(Y1+Y2) where Y2=0
        Z=piのとき
        r13=sin(Y1-Y2), r33=cos(Y1-Y2) where Y2=0
        Returns:
            Tuple[float, float, float]: YZY euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ay1_rad, az_rad, ay2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r22=cos(Z)の値で場合分け
        if near_zero(r22 - 1.0, eps=self.gimbal_eps):
            # r22 == +1, Z=0
            ay1_rad = math.atan2(r13, r33)
            az_rad = 0.0
            ay2_rad = 0.0 # Z軸のジンバルロックに従属
        elif near_zero(r22 + 1.0, eps=self.gimbal_eps):
            # r22 == -1, Z=pi
            ay1_rad = math.atan2(r13, r33)
            az_rad = math.pi
            ay2_rad = 0.0 # Z軸のジンバルロックに従属
        else:
            # -1 < r22 < +1
            ay1_rad = math.atan2(r32, -r12)
            az_rad = math.acos(r22)
            ay2_rad = math.atan2(r23, r21)

        # YZY euler
        return (ay1_rad, az_rad, ay2_rad)


# 内因性 ZXZ(Z1XZ2)
class EulerInnerZXZState(EulerState):

    def __init__(self):
        super(EulerInnerZXZState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return az_rot(theta1_rad) @ ax_rot(theta2_rad) @ az_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        X軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Z1)@R(X)@R(Z2)

            [[C(Z1)C(Z2)-C(X)S(Z1)S(Z2), -C(Z1)S(Z2)-C(X)C(Z2)S(Z1), S(Z1)S(X)],
             [C(Z2)S(Z1)+C(Z1)C(X)S(Z2), C(Z1)C(X)C(Z2)-S(Z1)S(Z2), -C(Z1)S(X)],
             [S(X)S(Z2), C(Z2)S(X), C(X)]]

            X=0のとき
            r11 = cos(Z1+Z2), r21 = sin(Z1+Z2) where Z2=0
            X=piのとき
            r11 = cos(Z1-Z2), r21 = sin(Z1-Z2) where Z2=0

        Returns:
            Tuple[float, float, float]: ZXZ euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        az1_rad, ax_rad, az2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r33=cos(X)の値で場合分け
        if near_zero(r33 - 1.0, eps=self.gimbal_eps):
            # r33 == +1, X=0
            az1_rad = math.atan2(r22, r11)
            ax_rad = 0.0
            az2_rad = 0.0 # X軸のジンバルロックに従属
        elif near_zero(r33 + 1.0, eps=self.gimbal_eps):
            # r33 == -1, X=pi
            az1_rad = math.atan2(r22, r11)
            ax_rad = math.pi
            az2_rad = 0.0 # X軸のジンバルロックに従属
        else:
            # -1 < r33 < +1
            az1_rad = math.atan2(r13, -r23)
            ax_rad = math.acos(r33)
            az2_rad = math.atan2(r31, r32)
        
        # ZXZ euler
        return (az1_rad, ax_rad, az2_rad)


# 内因性 ZYZ(Z1YZ2)
class EulerInnerZYZState(EulerState):

    def __init__(self):
        super(EulerInnerZYZState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
       
        return az_rot(theta1_rad) @ ay_rot(theta2_rad) @ az_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Y軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Z1)@R(Y)@R(Z2)

            [[C(Z1)C(Y)C(Z2)-S(Z1)S(Z2), -C(Z2)S(Z1)-C(Z1)C(Y)S(Z2), C(Z1)S(Y)],
             [C(Z1)S(Z2)+C(Y)C(Z2)S(Z1), C(Z1)C(Z2)-C(Y)S(Z1)S(Z2), S(Z1)S(Y)],
             [-C(Z2)S(Y), S(Y)S(Z2)-C(Y)S(Z1)S(Z2), S(Z1)S(Y)]]

            Y=0のとき
            r11 = cos(Z1+Z2), r21 = sin(Z1+Z2) where Z2=0
            Y=piのとき
            r11 = -cos(Z1-Z2), r21 = -sin(Z1-Z2) where Z2=0

        Returns:
            Tuple[float, float, float]: ZYZ euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        az1_rad, ay_rad, az2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r33=cos(Y)の値で場合分け
        if near_zero(r33 - 1.0, eps=self.gimbal_eps):
            # r33 == +1, Y=0
            az1_rad = math.degrees(math.atan2(r21, r11))
            ay_rad = 0.0
            az2_rad = 0.0 # Y軸のジンバルロックに従属
        elif near_zero(r33 + 1.0, eps=self.gimbal_eps):
            # r33 == -1, Y=pi
            az1_rad = math.degrees(math.atan2(r21, r11))
            ay_rad = math.degrees(math.pi)
            az2_rad = 0.0 # Y軸のジンバルロックに従属
        else:
            az1_rad = math.degrees(math.atan2(r23, r13))
            ay_rad = math.degrees(math.acos(r33))
            az2_rad = math.degrees(math.atan2(r32, -r31))

        # ZYZ Euler
        return (az1_rad, ay_rad, az2_rad)

# 内因性 XYZ
class EulerInnerXYZState(EulerState):

    def __init__(self):
        super(EulerInnerXYZState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ax_rot(theta1_rad) @ ay_rot(theta2_rad) @ az_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Y軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(X)@R(Y)@R(Z)

            [[C(Y)C(Z), -C(Y)S(Z), S(Y)],
             [C(X)S(Z)+C(Z)S(X)S(Y), C(X)C(Z)-S(X)S(Y)S(Z), -C(Y)S(X)],
             [S(X)S(Z)-C(X)C(Z)S(Y), C(Z)S(X)+C(X)S(Y)S(Z), C(X)C(Y)]]

            Y=+pi/2のとき
            r22 = cos(X+Z), r32 = sin(X+Z) where Z=0
            Y=-pi/2のとき
            r22 = cos(X-Z), r32 = sin(X-Z) where Z=0

        Returns:
            Tuple[float, float, float]: XYZ euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax_rad, ay_rad, az_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r13=sin(Y)の値で場合分け
        if near_zero(r13 - 1.0, eps=self.gimbal_eps):
            # r13 == +1, Y=pi/2
            ax_rad = math.atan2(r32, r22)
            ay_rad = math.pi/2
            az_rad = 0.0 # Y軸のジンバルロックに従属
        elif near_zero(r13 + 1.0, eps=self.gimbal_eps):
            # r13 == -1, Y=-pi/2
            ax_rad = math.atan2(r32, r22)
            ay_rad = -math.pi/2
            az_rad = 0.0 # Y軸のジンバルロックに従属
        else:
            # -1 < r13 < +1
            ax_rad = math.atan2(-r23, r33)
            ay_rad = math.asin(r13)
            az_rad = math.atan2(-r12, r11)

        # XYZ euler
        return (ax_rad, ay_rad, az_rad)
    

# 内因性 XZY
class EulerInnerXZYState(EulerState):

    def __init__(self):
        super(EulerInnerXZYState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ax_rot(theta1_rad) @ az_rot(theta2_rad) @ ay_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Z軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(X)@R(Z)@R(Y)

            [[C(Z)C(Y), -S(Z), C(Z)S(Y)],
             [S(X)S(Y)+C(X)C(Y)C(Z), C(X)C(Z), C(X)S(Z)S(Y)-C(Y)S(X)],
             [C(Y)S(X)S(Z)-C(X)S(Y), C(Z)S(X), C(X)C(Y)+S(X)S(Z)S(Y)]]

            Z=+pi/2のとき
            r21 = cos(X-Y), r31 = sin(X-Y) where Y=0
            Z=-pi/2のとき
            r21 = -cos(X+Y), r31 = -sin(X+Y) where Y=0

        Returns:
            Tuple[float, float, float]: XZY euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax_rad, ay_rad, az_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r12=-sin(Z)の値で場合分け
        if near_zero(r12 - 1.0, eps=self.gimbal_eps):
            # r12 == +1, Z=-pi/2
            ax_rad = math.atan2(r31, r21)
            az_rad = -math.pi/2
            ay_rad = 0.0 # Z軸のジンバルロックに従属
        elif near_zero(r12 + 1.0, eps=self.gimbal_eps):
            # r12 == -1, Z=pi/2
            ax_rad = math.atan2(r31, r21)
            az_rad = math.pi/2
            ay_rad = 0.0 # Z軸のジンバルロックに従属
        else:
            # -1 < r12 < +1
            ax_rad = math.atan2(r32, r22)
            az_rad = -math.asin(r12)
            ay_rad = math.atan2(r13, r11)

        # XZY euler
        return (ax_rad, az_rad, ay_rad)


# 内因性 YXZ
class EulerInnerYXZState(EulerState):

    def __init__(self):
        super(EulerInnerYXZState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ay_rot(theta1_rad) @ ax_rot(theta2_rad) @ az_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        X軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Y)@R(X)@R(Z)

            [[C(Y)C(Z)+S(Y)S(X)S(Z), C(Z)S(Y)S(X)-C(Y)S(Z), C(X)S(Y)],
             [C(X)S(Z), C(X)C(Z), -S(X)],
             [C(Y)S(X)S(Z)-C(Z)S(Y), C(Y)C(Z)S(X)+S(Y)S(Z), C(Y)C(X)]]

            X=+pi/2のとき
            r12=sin(Y-Z), r32=cos(Y-Z) where Z=0
            X=-pi/2のとき
            r12=-sin(Y+Z), r32=-cos(Y+Z) where Z=0

        Returns:
            Tuple[float, float, float]: YXZ euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax_rad, ay_rad, az_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r23=-sin(X)の値で場合分け
        if near_zero(r23, eps=self.gimbal_eps):
            # r23 == +1, X=-pi/2
            ay_rad = math.atan2(r12, r32)
            ax_rad = -math.pi/2
            az_rad = 0.0 # X軸のジンバルロックに従属
        elif near_zero(r23 + 1.0, eps=self.gimbal_eps):
            # r23 == -1, X=pi/2
            ay_rad = math.atan2(r12, r32)
            ax_rad = math.pi/2
            az_rad = 0.0 # X軸のジンバルロックに従属
        else:
            # -1 < r23 < +1
            ay_rad = math.atan2(r13, r33)
            ax_rad = -math.asin(r23)
            az_rad = math.atan2(r21, r22)

        # YXZ euler
        return (ay_rad, ax_rad, az_rad)


# 内因性 YZX
class EulerInnerYZXState(EulerState):

    def __init__(self):
        super(EulerInnerYZXState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ay_rot(theta1_rad) @ az_rot(theta2_rad) @ ax_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Z軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Y)@R(Z)@R(X)

            [[C(Y)C(Z), S(Y)S(X)-C(Y)C(X)S(Z), C(X)S(Y)+C(Y)S(Z)S(X)],
             [S(Z), C(Z)C(X), -C(Z)S(X)],
             [-C(Z)S(Y), C(Y)S(X)+C(X)S(Y)S(Z), C(Y)C(X)-S(Y)S(Z)S(X)]]

            Z=+pi/2のとき
            r13=sin(Y+X), r33=cos(Y+X) where X=0
            Z=-pi/2のとき
            r13=sin(Y-X), r33=cos(Y-X) where X=0

        Returns:
            Tuple[float, float, float]: YZX euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax_rad, ay_rad, az_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r21=sin(Z)の値で場合分け
        if near_zero(r21 - 1.0, eps=self.gimbal_eps):
            # r21 == +1, Z=pi/2
            ay_rad = math.atan2(r13, r33)
            az_rad = math.pi/2
            ax_rad = 0.0 # Z軸のジンバルロックに従属
        elif near_zero(r21 + 1.0, eps=self.gimbal_eps):
            # r21 == -1, Z=-pi/2
            ay_rad = math.atan2(r13, r33)
            az_rad = -math.pi_2
            ax_rad = 0.0 # Z軸のジンバルロックに従属
        else:
            # -1 < r21 < +1
            ay_rad = math.atan2(-r31, r11)
            az_rad = math.asin(r21)
            ax_rad = math.atan2(-r23, r22)

        # YZX euler
        return (ay_rad, az_rad, ax_rad)

# 内因性 ZXY
class EulerInnerZXYState(EulerState):

    def __init__(self):
        super(EulerInnerZXYState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return az_rot(theta1_rad) @ ax_rot(theta2_rad) @ ay_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        X軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Z)@R(X)@R(Y)

            [[C(Z)C(Y)-S(Z)S(X)S(Y), -C(X)S(Z), C(Z)S(Y)+C(Y)S(Z)S(X)],
             [C(Y)S(Z)+C(Z)S(X)S(Y), C(Z)C(X), S(Z)S(Y)-C(Z)C(X)S(Y)],
             [-C(X)S(Y), S(X), C(X)C(Y)]]

            X=+pi/2のとき
            r11=cos(Z+Y), r21=sin(Z+Y) where Y=0
            X=-pi/2のとき
            r11=cos(Z-Y), r21=sin(Z-Y) where Y=0

        Returns:
            Tuple[float, float, float]: ZXY euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax_rad, ay_rad, az_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r32=sin(X)の値をチェックして場合分け
        if near_zero(r32 - 1.0, eps=self.gimbal_eps):
            # r32 == +1, X=pi/2
            az_rad = math.atan2(r21, r11)
            ax_rad = math.pi/2
            ay_rad = 0.0 # X軸のジンバルロックに従属
        elif near_zero(r32 + 1.0, eps=self.gimbal_eps):
            # r32 == -1, X=-pi/2
            az_rad = math.atan2(r21, r11)
            ax_rad = -math.pi/2
            ay_rad = 0.0 # X軸のジンバルロックに従属
        else: 
            # -1 < r32 < +1
            az_rad = math.atan2(-r12, r22)
            ax_rad = math.asin(r32)
            ay_rad = math.atan2(-r31, r33)

        # ZXY euler
        return (az_rad, ax_rad, ay_rad)

# 内因性 ZYX
class EulerInnerZYXState(EulerState):
    
    def __init__(self):
        super(EulerInnerZYXState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return az_rot(theta1_rad) @ ay_rot(theta2_rad) @ ax_rot(theta3_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Y軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Z)@R(Y)@R(X)

            [[C(Z)C(Y), C(Z)S(Y)S(X)-C(X)S(Z), S(Z)S(X)+C(Z)C(X)S(Y)],
             [C(Y)S(Z), C(Z)C(X)+S(Z)S(Y)S(X), C(X)S(Z)S(Y)-C(Z)S(X)],
             [-S(Y), C(Y)S(X), C(Y)C(X)]]

            Y=+pi/2のとき
            r13=cos(Z-X), r23=sin(Z-X) where X=0
            Y=-pi/2のとき
            r13=-cos(Z+X), r23=-sin(Z+X) where X=0
            
        Returns:
            Tuple[float, float, float]: ZYX euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax_rad, ay_rad, az_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r31=-sin(Y)の値をチェックして場合分け
        if near_zero(r31 - 1.0, eps=self.gimbal_eps):
            # r31 == +1, Y=-pi/2
            az_rad = math.atan2(r23, r13)
            ay_rad = -math.pi/2
            ax_rad = 0.0 # Y軸回りのジンバルロックに従属
        elif near_zero(r31 + 1.0, eps=self.gimbal_eps):
            # r31 == -1, Y=pi/2
            az_rad = math.atan2(r23, r13)
            ay_rad = math.pi/2
            ax_rad = 0.0 # Y軸回りのジンバルロックに従属
        else: 
            # -1 < r31 < +1
            az_rad = math.atan2(r21, r11)
            ay_rad = -math.asin(r31)
            ax_rad = math.atan2(r32, r33)

        # ZYX euler
        return (az_rad, ay_rad, ax_rad)

# -----------------------------------------------------

# 外因性 XYX(X2YX1)
class EulerOuterXYXState(EulerState):

    def __init__(self):
        super(EulerOuterXYXState, self).__init__()
    
    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ax_rot(theta3_rad) @ ay_rot(theta2_rad) @ ax_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Y軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(X2)@R(Y)@R(X1)

        [[C(Y), S(Y)S(X1), C(X1)S(Y)],
         [S(X2)S(Y), C(X2)C(X1)-C(Y)S(X2)S(X1), -C(X2)S(X1)-C(Y)C(X1)S(X2)],
         [-C(X2)S(Y), C(X1)S(X2)+C(X2)C(Y)S(X1), C(X2)C(Y)C(X1)-S(X2)S(X1)]]

        Y=0のとき
        r22=cos(X1+X2), r32=sin(X1+X2)
        Z=piのとき
        r22=cos(X1-X2), r32=-sin(X1-X2)

        Returns:
            Tuple[float, float, float]: XYX euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax1_rad, ay_rad, ax2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r11=cos(Y)の値で場合分け
        if near_zero(r11 - 1.0, eps=self.gimbal_eps):
            # r11 == +1, Y=0
            ax1_rad = math.atan2(r32, r22)
            ay_rad = 0.0
            ax2_rad = 0.0 # Y軸のジンバルロックに従属
        elif near_zero(r11 + 1.0, eps=self.gimbal_eps):
            # r11 == -1, Y=pi
            ax1_rad = math.atan2(-r32, r22)
            ay_rad = math.pi
            ax2_rad = 0.0 # Y軸のジンバルロックに従属
        else:
            ax1_rad = math.atan2(r12, r13)
            ay_rad = math.acos(r11)
            ax2_rad = math.atan2(r21, -r31)
        
        # XYX Euler
        return (ax1_rad, ay_rad, ax2_rad)

# 外因性 XZX(X2ZX1)
class EulerOuterXZXState(EulerState):

    def __init__(self):
        super(EulerOuterXZXState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ax_rot(theta3_rad) @ az_rot(theta2_rad) @ ax_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Z軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(X2)@R(Z)@R(X1)

        [[C(Z), -C(X1)S(Z), S(Z)S(X1)],
         [C(X2)S(Z), C(X2)S(Z)C(X1)-S(X2)S(X1), -C(X1)S(X2)-C(X2)C(Z)S(X1)],
         [S(X2)S(Z), C(X2)S(X1)+C(Z)C(X1)S(X2), C(X2)C(X1)-C(Z)S(X2)S(X1)]]

        Z=0のとき
        r22=cos(X1+X2), r32=sin(X1+X2)
        Z=piのとき
        r22=-cos(X1-X2), r32=+sin(X1-X2)
        Returns:
            Tuple[float, float, float]: XZX euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ax1_rad, az_rad, ax2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r11=cos(Z)の値で場合分け
        if near_zero(r11 - 1.0, eps=self.gimbal_eps):
            # r11 == +1, Z=0
            ax1_rad = math.atan2(r32, r22)
            az_rad = 0.0 
            ax2_rad = 0.0 # Z軸のジンバルロックに従属
        elif near_zero(r11 + 1.0, eps=self.gimbal_eps):
            # r11 == -1, Z=pi
            ax1_rad = math.atan2(r32, -r22)
            az_rad = math.pi
            ax2_rad = 0.0 # Z軸のジンバルロックに従属
        else:
            ax1_rad = math.atan2(r13, -r12)
            az_rad = math.acos(r11)
            ax2_rad = math.atan2(r31, r21)

        # XZX euler
        return (ax1_rad, az_rad, ax2_rad)


# 外因性 YXY
class EulerOuterYXYState(EulerState):

    def __init__(self):
        super(EulerOuterYXYState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ay_rot(theta3_rad) @ ax_rot(theta2_rad) @ ay_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        X軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Y2)@R(X)@R(Y1)

        [[C(Y2)C(Y1)-C(X)S(Y2)S(Y1), S(Y2)S(X), C(Y2)S(Y1)+C(X)C(Y1)S(Y2)],
         [S(X)S(Y1), C(X), -C(Y1)S(X)],
         [-C(Y1)S(Y2)-C(Y2)C(X)S(Y1), C(Y2)S(X), C(Y2)C(X)C(Y1)-S(Y2)S(Y1)]]

        X=0のとき
        r13=sin(Y1+Y2), r33=cos(Y1+Y2)
        X=piのとき
        r13=+sin(Y1-Y2), r33=-cos(Y1-Y2)
        Returns:
            Tuple[float, float, float]: YXY euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ay1_rad, ax_rad, ay2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r22=cos(X)の値で場合分け
        if near_zero(r22 - 1.0, eps=self.gimbal_eps):
            # r22 == +1, X=0
            ay1_rad = math.atan2(r13, r33)
            ax_rad = 0.0
            ay2_rad = 0.0 # X軸のジンバルロックに従属
        elif near_zero(r22 + 1.0, eps=self.gimbal_eps):
            ay1_rad = math.atan2(r13, -r33)
            ax_rad = math.pi
            ay2_rad = 0.0 # X軸のジンバルロックに従属
        else:
            ay1_rad = math.atan2(r21, -r23)
            ax_rad = math.acos(r22)
            ay2_rad = math.atan2(r12, r32)
            
        # Euler YXY
        return (ay1_rad, ax_rad, ay2_rad)

# 外因性 YZY
class EulerOuterYZYState(EulerState):

    def __init__(self):
        super(EulerOuterYZYState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ay_rot(theta3_rad) @ az_rot(theta2_rad) @ ay_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Z軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Y2)@R(Z)@R(Y1)

        [[C(Y2)C(Z)C(Y1)-S(Y2)S(Y1), -C(Y2)S(Z), C(Y1)S(Y2)+C(Y2)C(Z)S(Y1)],
         [C(Y1)S(Z), C(Z), S(Z)S(Y1)],
         [-C(Y2)S(Y1)-C(Z)C(Y1)S(Y2), S(Y2)S(Z), C(Y2)C(Y1)-C(Z)S(Y2)S(Y1)]]

        Z=0のとき
        r13=sin(Y1+Y2), r33=cos(Y1+Y2)
        Z=piのとき
        r13=-sin(Y1-Y2), r33=cos(Y1-Y2)
        Returns:
            Tuple[float, float, float]: YZY euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ay1_rad, az_rad, ay2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r22=cos(Z)の値で場合分け
        if near_zero(r22 - 1.0, eps=self.gimbal_eps):
            # r22 == +1, Z=0
            ay1_rad = math.atan2(r13, r33)
            az_rad = 0.0
            ay2_rad = 0.0 # Z軸のジンバルロックに従属
        elif near_zero(r22 + 1.0, eps=self.gimbal_eps):
            # r22 == -1, Z=pi
            ay1_rad = math.atan2(-r13, r33)
            az_rad = math.pi
            ay2_rad = 0.0 # Z軸のジンバルロックに従属
        else:
            ay1_rad = math.atan2(r23, r21)
            az_rad = math.acos(r22)
            ay2_rad = math.atan2(r32, -r12)
            
        # YZY euler
        return (ay1_rad, az_rad, ay2_rad)

# 外因性 ZXZ
class EulerOuterZXZState(EulerState):

    def __init__(self):
        super(EulerOuterZXZState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return az_rot(theta3_rad) @ ax_rot(theta2_rad) @ az_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        X軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Z2)@R(X)@R(Z1)

            [[C(Z2)C(Z1)-C(X)S(Z2)S(Z1), -C(Z2)S(Z1)-C(X)C(Z1)S(Z2), S(Z2)S(X)],
             [C(Z1)S(Z2)+C(Z2)C(X)S(Z1), C(Z2)C(X)C(Z1)-S(Z2)S(Z1), -C(Z2)S(X)],
             [S(X)S(Z1), C(Z1)S(X), C(X)]]

            X=0のとき
            r11 = cos(Z1+Z2), r21 = sin(Z1+Z2) where Z2=0
            X=piのとき
            r11 = cos(Z1-Z2), r21 = +sin(Z1-Z2) where Z2=0

        Returns:
            Tuple[float, float, float]: ZXZ euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        az1_rad, ax_rad, az2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r33=cos(X)の値で場合分け
        if near_zero(r33 - 1.0, eps=self.gimbal_eps):
            # r33 == +1, X=0
            az1_rad = math.atan2(r22, r11)
            ax_rad = 0.0
            az2_rad = 0.0 # X軸のジンバルロックに従属
        elif near_zero(r33 + 1.0, eps=self.gimbal_eps):
            # r33 == -1, X=pi
            az1_rad = math.atan2(-r22, r11)
            ax_rad = math.pi
            az2_rad = 0.0 # X軸のジンバルロックに従属
        else:
            az1_rad = math.atan2(r31, r32)
            ax_rad = math.acos(r33)
            az2_rad = math.atan2(r13, -r23)
        
        # ZXZ euler
        return (az1_rad, ax_rad, az2_rad)

# 外因性 ZYZ
class EulerOuterZYZState(EulerState):

    def __init__(self):
        super(EulerOuterZYZState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return az_rot(theta3_rad) @ ay_rot(theta2_rad) @ az_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Y軸回りの回転が0,πのときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Z2)@R(Y)@R(Z1)

            [[C(Z1)C(Y)C(Z2)-S(Z1)S(Z2), -C(Z2)S(Z1)-C(Z1)C(Y)S(Z2), C(Z1)S(Y)],
             [C(Z1)S(Z2)+C(Y)C(Z2)S(Z1), C(Z1)C(Z2)-C(Y)S(Z1)S(Z2), S(Z1)S(Y)],
             [-C(Z2)S(Y), S(Y)S(Z2)-C(Y)S(Z1)S(Z2), S(Z1)S(Y)]]

            Y=0のとき
            r11 = cos(Z1+Z2), r21 = sin(Z1+Z2) where Z2=0
            Y=piのとき
            r11 = -cos(Z1-Z2), r21 = +sin(Z1-Z2) where Z2=0

        Returns:
            Tuple[float, float, float]: ZYZ euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        az1_rad, ay_rad, az2_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r33=cos(Y)の値で場合分け
        if near_zero(r33 - 1.0, eps=self.gimbal_eps):
            # r33 == +1, Y=0
            az1_rad = math.atan2(r21, r11)
            ay_rad = 0.0
            az2_rad = 0.0 # Y軸のジンバルロックに従属
        elif near_zero(r33 + 1.0, eps=self.gimbal_eps):
            # r33 == -1, Y=pi
            az1_rad = math.atan2(r21, -r11)
            ay_rad = math.pi
            az2_rad = 0.0 # Y軸のジンバルロックに従属
        else:
            az1_rad = math.atan2(r32, -r31)
            ay_rad = math.acos(r33)
            az2_rad = math.atan2(r23, r13)

        # ZYZ Euler
        return (az1_rad, ay_rad, az2_rad)

# 外因性 XYZ
class EulerOuterXYZState(EulerState):

    def __init__(self):
        super(EulerOuterXYZState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return az_rot(theta3_rad) @ ay_rot(theta2_rad) @ ax_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Y軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Z)@R(Y)@R(X)

            [[C(Z)C(Y), C(Z)S(Y)S(X)-C(X)S(Z), S(Z)S(X)+C(Z)C(X)S(Y)],
             [C(Y)S(Z), C(Z)C(X)+S(Z)S(Y)S(X), C(X)S(Z)S(Y)-C(Z)S(X)],
             [-S(Y), C(Y)S(X), C(Y)C(X)]]

            Y=+pi/2のとき
            r13 = cos(X-Z), r23 = sin(X-Z) where Z=0
            Y=-pi/2のとき
            r13 = -cos(X+Z), r23 = -sin(X+Z) where Z=0

        Returns:
            Tuple[float, float, float]: XYZ euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        az_rad, ay_rad, ax_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r31=-sin(Y)の値で場合分け
        if near_zero(r31 - 1.0, eps=self.gimbal_eps):
            # r31 == +1, Y=-pi/2
            ax_rad = math.atan2(r21, r11)
            ay_rad = -math.pi/2
            az_rad = 0.0 # Y軸のジンバルロックに従属
        elif near_zero(r31 + 1.0, eps=self.gimbal_eps):
            # r31 == -1, Y=pi/2
            ax_rad = math.atan2(r21, r11)
            ay_rad = math.pi/2
            az_rad = 0.0 # Y軸のジンバルロックに従属
        else:
            ax_rad = math.atan2(r32, r33)
            ay_rad = -math.asin(r31)
            az_rad = math.atan2(r21, r11)

        # XYZ Euler
        return (ax_rad, ay_rad, az_rad)


# 外因性 XZY
class EulerOuterXZYState(EulerState):

    def __init__(self):
        super(EulerOuterXZYState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ay_rot(theta3_rad) @ az_rot(theta2_rad) @ ax_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Z軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Y)@R(Z)@R(X)

            [[C(Y)C(Z), S(Y)S(X)-C(Y)C(X)S(Z), C(X)S(Z)+C(Y)S(Z)S(X)],
             [S(Z), C(Z)C(X), -C(Z)S(X)],
             [-C(Z)S(Y), C(Y)S(X)+C(X)S(Y)S(Z), C(Y)C(X)-S(Y)S(Z)S(X)]]

            Z=+pi/2のとき
            r13 = sin(X+Y), r33 = cos(X+Y) where Y=0
            Z=-pi/2のとき
            r13 = -sin(X-Y), r33 = cos(X-Y) where Y=0

        Returns:
            Tuple[float, float, float]: XZY euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        az_rad, ay_rad, ax_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r21=sin(Z)の値で場合分け
        if near_zero(r21 - 1.0, eps=self.gimbal_eps):
            # r21 == +1, Z=pi/2
            ax_rad = math.atan2(r11, r33)
            az_rad = math.pi/2
            ay_rad = 0.0 # Z軸のジンバルロックに従属
        elif near_zero(r21 + 1.0, eps=self.gimbal_eps):
            # r21 == -1, Y=-pi/2
            ax_rad = math.atan2(-r11, r33)
            az_rad = -math.pi/2
            ay_rad = 0.0 # Z軸のジンバルロックに従属
        else:
            ax_rad = math.atan2(-r23, r22)
            az_rad = math.asin(r21)
            ay_rad = math.atan2(-r31, r11)

        # XZY Euler
        return (ax_rad, az_rad, ay_rad)

# 外因性 YXZ
class EulerOuterYXZState(EulerState):

    def __init__(self):
        super(EulerOuterYXZState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return az_rot(theta3_rad) @ ax_rot(theta2_rad) @ ay_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        X軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Z)@R(X)@R(Y)

            [[C(Z)C(Y)-S(Z)S(X)S(Y), -C(X)S(Z), C(Z)S(Y)+C(Y)S(Z)S(X)],
             [C(Y)S(Z)+C(Z)S(X)S(Y), C(Z)C(X), S(Z)S(Y)-C(Z)C(Y)S(X)],
             [-C(X)S(Y), S(X), C(X)C(Y)]]

            Z=+pi/2のとき
            r11 = cos(Y+Z), r21 = sin(Y+Z) where Z=0
            Z=-pi/2のとき
            r11 = cos(Y-Z), r21 = -sin(Y-Z) where Z=0

        Returns:
            Tuple[float, float, float]: YXZ euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ay_rad, ax_rad, az_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r32=sin(X)の値で場合分け
        if near_zero(r32 - 1.0, eps=self.gimbal_eps):
            # r32 == +1, X=pi/2
            ay_rad = math.atan2(r21, r11)
            ax_rad = math.pi/2
            az_rad = 0.0 # X軸のジンバルロックに従属
        elif near_zero(r32 + 1.0, eps=self.gimbal_eps):
            # r32 == -1, Y=-pi/2
            ay_rad = math.atan2(-r21, r11)
            ax_rad = -math.pi/2
            az_rad = 0.0 # X軸のジンバルロックに従属
        else:
            ay_rad = math.atan2(-r31, r33)
            ax_rad = math.asin(r32)
            az_rad = math.atan2(-r21, r22)

        # YXZ Euler
        return (ay_rad, ax_rad, az_rad)

# 外因性 YZX
class EulerOuterYZXState(EulerState):

    def __init__(self):
        super(EulerOuterYZXState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ax_rot(theta3_rad) @ az_rot(theta2_rad) @ ay_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        Z軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(X)@R(Z)@R(Y)

            [[C(Z)C(Y), -S(Z), C(Z)S(Y)],
             [S(X)S(Y)+C(X)C(Y)S(Z), C(X)C(Z), C(X)S(Z)S(Y)-C(Y)S(X)],
             [C(Y)S(X)S(Z)-C(X)S(Y), C(Z)S(X), C(X)C(Y)+S(X)S(Z)S(Y)]]

            Z=+pi/2のとき
            r21 = +cos(Y-X), r31 = -sin(Y-X) where X=0
            Z=-pi/2のとき
            r21 = -cos(Y+X), r31 = -sin(Y+X) where X=0

        Returns:
            Tuple[float, float, float]: YZX euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        ay_rad, az_rad, ax_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r12=-sin(Z)の値で場合分け
        if near_zero(r12 - 1.0, eps=self.gimbal_eps):
            # r12 == +1, Z=-pi/2
            ay_rad = math.atan2(-r31, r21)
            az_rad = -math.pi/2
            ax_rad = 0.0 # Z軸のジンバルロックに従属
        elif near_zero(r12 + 1.0, eps=self.gimbal_eps):
            # r12 == -1, Z=pi/2
            ay_rad = math.atan2(r31, r21)
            az_rad = math.pi/2
            ax_rad = 0.0 # Z軸のジンバルロックに従属
        else:
            ay_rad = math.atan2(r13, r11)
            az_rad = -math.asin(r12)
            ax_rad = math.atan2(r32, r22)

        # YZX Euler
        return (ay_rad, az_rad, ax_rad)


# 外因性 ZXY
class EulerOuterZXYState(EulerState):

    def __init__(self):
        super(EulerOuterZXYState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ay_rot(theta3_rad) @ ax_rot(theta2_rad) @ az_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        X軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(Y)@R(X)@R(Z)

            [[C(Y)C(Z)+S(Y)S(X)S(Z), C(Z)S(Y)S(X)-C(Y)S(Z), C(X)S(Y)],
             [C(X)S(Z), C(X)C(Z), -S(X)],
             [C(Y)S(X)S(Z)-C(Z)S(Y), C(Y)C(Z)S(X)+S(Y)S(Z), C(Y)C(X)]]

            X=+pi/2のとき
            r12 = -sin(Z-Y), r32 = cos(Z-Y) where Y=0
            X=-pi/2のとき
            r12 = -sin(Z+Y), r32 = -cos(Z+Y) where Y=0

        Returns:
            Tuple[float, float, float]: ZXY euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        az_rad, ax_rad, ay_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r23=-sin(X)の値で場合分け
        if near_zero(r23 - 1.0, eps=self.gimbal_eps):
            # r23 == +1, X=-pi/2
            az_rad = math.atan2(r12, r32)
            ax_rad = -math.pi/2
            ay_rad = 0.0 # X軸のジンバルロックに従属
        elif near_zero(r23 + 1.0, eps=self.gimbal_eps):
            # r23 == -1, X=pi/2
            az_rad = math.atan2(-r12, r32)
            ax_rad = math.pi/2
            ay_rad = 0.0 # Z軸のジンバルロックに従属
        else:
            az_rad = math.atan2(r21, r22)
            ax_rad = -math.asin(r23)
            ay_rad = math.atan2(r13, r33)

        # ZXY Euler
        return (az_rad, ax_rad, ay_rad)

# 外因性 ZYX
class EulerOuterZYXState(EulerState):
    
    def __init__(self):
        super(EulerOuterZYXState, self).__init__()

    @EulerState.overrides(EulerState)
    def to_rot(self,
               theta1_rad: float,
               theta2_rad: float,
               theta3_rad: float) -> np.ndarray:
        
        return ax_rot(theta3_rad) @ ay_rot(theta2_rad) @ az_rot(theta1_rad)
    
    @EulerState.overrides(EulerState)
    def from_rot(self,
                 rot: np.ndarray) -> Tuple[float, float, float]:
        """回転行列からオイラー角を計算
        X軸回りの回転が±π/2のときジンバルロック発生.

        Args:
            rot (np.ndarray): 回転行列

            R_global = R(X)@R(Y)@R(Z)

            [[C(Y)C(Z), -C(Y)S(Z), S(Y)],
             [C(X)S(Z)+C(Z)S(X)S(Y), C(X)C(Z)-S(X)S(Y)S(Z), -C(Y)S(X)],
             [S(X)S(Z)-C(X)C(Z)S(Y), C(Z)S(X)+C(X)S(Y)S(Z), C(X)C(Y)]]

            Y=+pi/2のとき
            r22 = cos(Z+X), r32 = sin(Z+X) where X=0
            Y=-pi/2のとき
            r22 = cos(Z-X), r32 = -sin(Z-Y) where X=0

        Returns:
            Tuple[float, float, float]: ZYX euler
        """
        if rot.shape != (3,3):
            raise ValueError(f"Not match shape (3,3). Given is {rot.shape}")
        
        r11, r12, r13 = rot[0,0], rot[0,1], rot[0,2]
        r21, r22, r23 = rot[1,0], rot[1,1], rot[1,2]
        r31, r32, r33 = rot[2,0], rot[2,1], rot[2,2]

        az_rad, ay_rad, ax_rad = 0.0, 0.0, 0.0

        # ジンバルロックの確認
        # r13=sin(Y)の値で場合分け
        if near_zero(r13 - 1.0, eps=self.gimbal_eps):
            # r13 == +1, Y=pi/2
            az_rad = math.atan2(r32, r22)
            ay_rad = math.pi/2
            ax_rad = 0.0 # Y軸のジンバルロックに従属
        elif near_zero(r13 + 1.0, eps=self.gimbal_eps):
            # r13 == -1, Y=-pi/2
            az_rad = math.atan2(-r32, r22)
            ay_rad = -math.pi/2
            ax_rad = 0.0 # Y軸のジンバルロックに従属
        else:
            az_rad = math.atan2(-r12, r11)
            ax_rad = math.asin(r13)
            ay_rad = math.atan2(-r23, r33)

        # ZYX Euler
        return (az_rad, ay_rad, ax_rad)
    
    