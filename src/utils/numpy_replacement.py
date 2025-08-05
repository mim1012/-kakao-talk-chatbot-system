"""
numpy 대체 모듈 - 기본 기능만 제공
"""
import math
from typing import Union, List, Tuple, Any

class ndarray:
    """numpy.ndarray 대체 클래스"""
    def __init__(self, data, dtype=None):
        if isinstance(data, list):
            self.data = data
        else:
            self.data = [data]
        self.dtype = dtype or 'float64'
        
        # 차원 계산
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], list):
                self.shape = (len(data), len(data[0]))
            else:
                self.shape = (len(data),)
        else:
            self.shape = (1,)
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __len__(self):
        return len(self.data)

def array(data, dtype=None):
    """numpy.array 대체 함수"""
    return ndarray(data, dtype)

def zeros(shape, dtype='float64'):
    """numpy.zeros 대체"""
    if isinstance(shape, int):
        return ndarray([0] * shape, dtype)
    elif isinstance(shape, tuple) and len(shape) == 2:
        return ndarray([[0] * shape[1] for _ in range(shape[0])], dtype)
    else:
        return ndarray([0], dtype)

def ones(shape, dtype='float64'):
    """numpy.ones 대체"""
    if isinstance(shape, int):
        return ndarray([1] * shape, dtype)
    elif isinstance(shape, tuple) and len(shape) == 2:
        return ndarray([[1] * shape[1] for _ in range(shape[0])], dtype)
    else:
        return ndarray([1], dtype)

def uint8():
    """numpy.uint8 타입"""
    return 'uint8'

def float64():
    """numpy.float64 타입"""
    return 'float64'

# 호환성을 위한 변수들
__version__ = "1.26.4 (compatible replacement)"
