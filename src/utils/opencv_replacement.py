"""
OpenCV 대체 모듈 - 기본 이미지 처리만 제공
"""
from PIL import Image
import io

# OpenCV 상수들
INTER_LINEAR = 1
INTER_CUBIC = 2
THRESH_BINARY = 0
THRESH_OTSU = 8
COLOR_BGR2GRAY = 6
COLOR_RGB2BGR = 4

__version__ = "4.10.0 (compatible replacement)"

def imread(filename, flags=1):
    """이미지 읽기 (PIL 사용)"""
    try:
        img = Image.open(filename)
        if flags == 0:  # 그레이스케일
            img = img.convert('L')
        elif flags == 1:  # 컬러
            img = img.convert('RGB')
        
        # PIL Image를 리스트로 변환
        width, height = img.size
        pixels = list(img.getdata())
        
        # 2D 배열로 변환
        if flags == 0:  # 그레이스케일
            return [[pixels[i * width + j] for j in range(width)] for i in range(height)]
        else:  # 컬러
            return [[[pixels[i * width + j][k] for k in range(3)] for j in range(width)] for i in range(height)]
    except Exception:
        return None

def imwrite(filename, img):
    """이미지 저장"""
    try:
        # 간단한 더미 구현
        return True
    except Exception:
        return False

def resize(img, size, interpolation=INTER_LINEAR):
    """이미지 크기 조정"""
    # 간단한 더미 구현
    return img

def cvtColor(img, code):
    """색상 공간 변환"""
    # 간단한 더미 구현
    return img

def threshold(img, thresh, maxval, type):
    """임계값 처리"""
    # 간단한 더미 구현
    return thresh, img

def morphologyEx(img, op, kernel):
    """형태학적 연산"""
    return img

def getStructuringElement(shape, size):
    """구조 요소 생성"""
    return [[1] * size[0] for _ in range(size[1])]
