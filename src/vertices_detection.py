import cv2
import numpy as np
import logging

from matplotlib import pyplot as plt
import matplotlib

# matplotlib.use('TKAgg')

from numpy.linalg import norm

from OmrExceptions import *

# from omr_utils import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def otsu_filter(img, blur_kernel=1):
    blur = cv2.medianBlur(img, blur_kernel, 0)  # TODO adjust the kernel
    _, th3 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return th3


def crop_to_four(image, h=None, w=None):
    if h is None:
        h = int(image.shape[0] / 2)
    if w is None:
        w = int(image.shape[1] / 2)
    # h, w = half_height_width(image)
    return image[0:h, 0: w], \
           image[0: h, w:], \
           image[h:, 0:w], \
           image[h:, w:]


def check_side(side_nz_array):
    return side_nz_array[-1] - side_nz_array[0] == len(side_nz_array) - 1


def get_side(image, axis=1):
    side = np.argmax(image, axis=axis)
    if np.any(image):
        nz = np.nonzero(side)[0]
        if len(nz) > 0 and nz[-1] - nz[0] == len(nz) - 1:
            return side, side[nz], nz
    raise GetSideException(f"Get Side Exception on axis={axis}")


def get_vertex(image, axis, debug=False):
    side, side_nz, nz = get_side(image, axis)
    height, width = image.shape
    point_a = np.array([nz[0], image.shape[1 - axis]])  # image.shape[1 - axis]
    point_b = np.array([nz[-1], side_nz[-1]])  # [image.shape[axis]

    point = get_max_distant_point(nz, side_nz, point_a, point_b)
    result = (point[axis], point[1 - axis])
    if debug:
        plt.subplot(141), plt.imshow(image, 'gray'), plt.title(f'quarter axis={axis}')
        plt.subplot(142), plt.plot(side), plt.title(f'side')
        plt.subplot(143), plt.plot(side_nz), plt.title(f'side_nz')
        plt.subplot(144), plt.plot(nz, side_nz, 'r'), plt.title(f'result {result}')
        plt.show()
    return result  # point[axis], point[1 - axis]


def tp(arr):
    return arr[0], arr[1]


def get_vertex_crossing(image, axis, debug=False):
    side, side_nz, nz = get_side(image, axis)
    height, width = image.shape
    a = np.array([nz[0], image.shape[axis]])
    # b = np.array([nz[-1], side_nz[-1]])
    b = np.array([nz[-1], side_nz[-1]])
    point = get_max_distant_point(nz, side_nz, a, b)
    result = (point[axis], point[1 - axis])
    if debug:
        image = image.copy()
        print(f'a = {a}, b = {b}')
        cv2.circle(image, tp(a), 30, (255, 0, 255), 15)
        cv2.circle(image, tp(b), 30, (255, 0, 255), 15)
        plt.subplot(141), plt.imshow(image, 'gray'), plt.title(f'qtr axis={axis}')
        plt.subplot(142), plt.plot(side), plt.title(f'side')
        plt.subplot(143), plt.plot(side_nz), plt.title(f'side_nz')
        plt.subplot(144), plt.plot(nz, side_nz, 'r'), plt.title(f'result {result}')
        plt.show()
    return result  # point[axis], point[1 - axis]


def vertex(image, debug=False):
    for axis in [1, 0]:
        try:
            return get_vertex_crossing(image, axis, debug)
        except GetSideException:
            logger.debug(f"GetSideException axis={axis}")
    raise GetSideException(f"Both V & H sides exceptions")


def normalize_quarters(tpl):
    return tpl[0], \
           np.fliplr(tpl[1]), \
           np.flipud(tpl[2]), \
           tpl[3][::-1, ::-1]
    # np.fliplr(np.flipud(tpl[3]))


def get_max_distant_point(x, y, a=None, b=None):
    """
    Given "ab" line segment and collection of ordered points with coordinates x and y, choose the point
    which has the maximum distant from the line passes through "ab",
    if "a" and "b" were not given then set "a" point to be the first point of the collection
    and "b" point to be the last one

    :param x: np.array([int,...int]), x coordinates of points.
    :param y: np.array([int,...int]), y coordinates of points.
    :param a: np.array([int, int]), optional, edge of line segment,
        if None then set it to the first point (x0, y0)
    :param b: np.array([int, int]), optional, edge of line segment,
        if None then set it to the last point (x0, y0)
    :return:np.array([int, int]) max distant point from "ab" segment
    """
    if len(x) == 0 or len(y) == 0:
        raise Exception(f"len(x) = {len(x)}, len(y) = {len(y)}")
    if a is None:
        try:
            a = np.array([x[0], y[0]])
        except:
            print(f"x = {x}, y = {y}")

    if b is None:
        b = np.array([x[-1], y[-1]])
    points = np.column_stack((x, y))
    distances = [distance(a, b, p) for p in points]
    mx_index = np.argmax(distances)
    return x[mx_index], y[mx_index]


def distance(a, b, p):
    """Distance between point "p" and line of "ab"

    :param a: np.array([int, int]) first edge a of segment line "ab".
    :param b: np.array([int, int]) second edge a of segment line "ab"
    :param p: np.array([int, int])
    :return: real, the distance from point "p" to line passes through "ab" segment
    """
    if all(a == p) or all(b == p):  # TODO unnecessary check, write tests to test optimization benefit of it
        return 0
    return norm(np.cross(b - a, a - p)) / norm(b - a)


def vertices_stacked(vrtcs, height, width, h=None, w=None):
    if h is None:
        h = int(height / 2)
    if w is None:
        w = int(width / 2)
    return [vrtcs[0],
            (width - vrtcs[1][0], vrtcs[1][1]),
            (vrtcs[2][0], height - vrtcs[2][1]),
            (width - vrtcs[3][0], height - vrtcs[3][1])]


def vertices(image, debug=False):
    height, width = image.shape
    # h, w = int(height / 2), int(width / 2)
    # im_list = normalize_quarters(crop_to_four(image, h, w))
    im_list = normalize_quarters(crop_to_four(image))
    vrtcs = [vertex(im, debug) for im in im_list]
    print(vrtcs)
    if debug:
        for idx, img in enumerate(im_list):
            img = img.copy()
            cv2.circle(img, vrtcs[idx], 50, (255, 255, 255), 5)
            plt.subplot(221 + idx), plt.imshow(img, 'gray'), plt.title(f'q {idx + 1}')

        plt.show()
    # return vertices_stacked(vrtcs, height, width, h, w)
    return vertices_stacked(vrtcs, height, width)


def transform(img, vertices, shape, show=False):
    """
     Wrap the region of answer sheet inside "img" into new image image with fized size defined in "shape"

    :param img: opencv image, gray, contains the answer sheet
    :param vertices: List, four point vertices of the answer sheet
    :param shape: array[width, height], size of resulting image
    :param show: boolean, for debugging purposes TODO delete later
    :return: opencv image, fixed size as in shape
    """
    pts1 = np.float32(vertices)

    # pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
    pts2 = np.float32([[0, 0], [shape[0], 0], [0, shape[1]], shape])

    m_transform = cv2.getPerspectiveTransform(pts1, pts2)
    dst = cv2.warpPerspective(img, m_transform, tuple(shape))

    if show:  # TODO delete later
        plt.subplot(121), plt.imshow(img, 'gray'), plt.title('Input')
        plt.subplot(122), plt.imshow(dst, 'gray'), plt.title('Output')
        plt.show()
    return dst


def crop_margin(image, y_margin, x_margin=None):
    if x_margin is None:
        x_margin = y_margin
    return image[y_margin:-y_margin, x_margin: -x_margin]


def border_filter(img):
    return otsu_filter(img, blur_kernel=17)


def get_sheet(img, debug=False):
    img_otsu = border_filter(img)
    vtcs = vertices(img_otsu, debug)
    image_vis = transform(img, vtcs, (1020, 1520), show=False)
    image_vis = crop_margin(image_vis, 10)
    plt.imshow(image_vis, 'gray')
    plt.show()
    return image_vis



def test():
    file_path = '../data/in/12.jpg'
    img = cv2.imread(file_path, 0)
    get_sheet(img, False)



if __name__ == '__main__':
    import timeit
    print(timeit.timeit(test, number=1))
