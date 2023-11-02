"""
Implementation of SORT("SIMPLE ONLINE AND REALTIME TRACKING")
https://arxiv.org/pdf/1602.00763.pdf
"""

import numpy as np
from scipy.optimize import linear_sum_assignment


# list of preset colors
COLOR_MAP = [
    (246, 13, 26),
    (255, 153, 51),
    (80, 238, 171),
    (117, 243, 84),
    (217, 83, 252),
    (132, 78, 235),
    (204, 204, 51),
    (255, 255, 153),
    (244, 76, 134),
    (251, 80, 205),
]


"""
* Formulation of Kalman Filter
SORT uses 7dim state x=[u,v,s,r,du,dv,ds] where
- u,v: center of bbox
- s: area of the bbox
- r: aspect ratio of the bbox
- du,dv,ds: velocity of variables respect to 1 frame
and 4dim measurement z=[u,v,s,r]

State transltion
u(k+1) = u(k) + du(k)
v(k+1) = v(k) + dv(k)
s(k+1) = s(k) + ds(k)
r(k+1) = r(k)
du(k+1) = du(k)
dv(k+1) = dv(k)
ds(k+1) = ds(k)
"""

# State transition matrix
F = np.array(
    [
        [1, 0, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [0, 0, 1, 0, 0, 0, 1],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 1],
    ]
)

# Measurement matrix
H = np.array(
    [
        [1, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
    ]
)

# Diagonal of covariance matrix for measurement noise
R = np.diag([10, 10, 10, 10])

# Covariance matrix for state transition noise
Q = np.diag([1, 1, 1, 1, 1e-2, 1e-2, 1e-4])

# Initial covariance matrix for estimation error
P0 = np.diag([10, 10, 10, 10, 1e4, 1e4, 1e4])


def bbox_to_z(bbox):
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0
    return [x0 + w / 2, y0 + h / 2, w * h, w / h]


def x_to_bbox(x):
    u, v, s, r, du, dv, ds = x
    w = np.sqrt(s * r)
    h = s / w
    return [u - w / 2, v - h / 2, u + w / 2, v + h / 2]


def compute_ious(bboxes0, bboxes1, margin):
    bboxes0 = np.array(bboxes0).reshape(-1, 1, 4)
    bboxes1 = np.array(bboxes1).reshape(1, -1, 4)

    w0 = bboxes0[:, :, 2] - bboxes0[:, :, 0]
    h0 = bboxes0[:, :, 3] - bboxes0[:, :, 1]
    bboxes0[:, :, 0] -= w0 * margin
    bboxes0[:, :, 1] -= h0 * margin
    bboxes0[:, :, 2] += w0 * margin
    bboxes0[:, :, 3] += h0 * margin

    w1 = bboxes1[:, :, 2] - bboxes1[:, :, 0]
    h1 = bboxes1[:, :, 3] - bboxes1[:, :, 1]
    bboxes1[:, :, 0] -= w1 * margin
    bboxes1[:, :, 1] -= h1 * margin
    bboxes1[:, :, 2] += w1 * margin
    bboxes1[:, :, 3] += h1 * margin

    tl = np.maximum(bboxes0[:, :, :2], bboxes1[:, :, :2])  # top left
    br = np.minimum(bboxes0[:, :, 2:], bboxes1[:, :, 2:])  # bottom right
    isect = np.prod(tl - br, axis=2) * (tl < br).all(axis=2)
    area0 = np.prod(bboxes0[:, :, 2:] - bboxes0[:, :, :2], axis=2)
    area1 = np.prod(bboxes1[:, :, 2:] - bboxes1[:, :, :2], axis=2)
    ious = isect / (area0 + area1 - isect)
    return ious


class Tracker(object):
    def __init__(
        self,
        width,
        height,
        detection_area_margin=0.0,
        max_misscount=10,
        bbox_margin=1.0,
        iou_threshold=0.1,
    ):
        self.nextid = 0
        self.area_xmin = int(width * detection_area_margin)
        self.area_xmax = int(width * (1 - detection_area_margin))
        self.area_ymin = int(height * detection_area_margin)
        self.area_ymax = int(height * (1 - detection_area_margin))
        self.max_misscount = max_misscount
        self.bbox_margin = bbox_margin
        self.iou_threshold = iou_threshold
        self.tracklets = []  # (x, P, id, miss, detected)

    def predict_KF(self):
        for i, (x, P, id, miss, detected) in enumerate(self.tracklets):
            x = F.dot(x)
            P = F.dot(P).dot(F.T) + Q

            if x[2] < 0:  # area
                x[2] = 0

            self.tracklets[i] = x, P, id, miss, detected

    def update_KF(self, observations):
        for i, bbox in enumerate(observations):
            x, P, id, miss, detected = self.tracklets[i]
            if bbox is None:
                miss += 1
            else:
                miss = 0
                z = bbox_to_z(bbox)
                e = z - H.dot(x)
                S = R + H.dot(P).dot(H.T)
                K = P.dot(H.T).dot(np.linalg.inv(S))
                x = x + K.dot(e)
                P = (np.eye(7) - K.dot(H)).dot(P)

            self.tracklets[i] = x, P, id, miss, detected

    def update(self, faces, it=0):
        ret = []
        bboxes0 = [bbox for c, bbox, _ in faces]

        # proceed KF 1 step
        self.predict_KF()

        # Remove missing bboxes
        self.tracklets = [
            (x, P, id, miss, detected)
            for x, P, id, miss, detected in self.tracklets
            if miss < self.max_misscount and x[2] > 0
        ]

        # Compute matching between detections and tracklets
        bboxes1 = [x_to_bbox(x) for x, _, _, _, _ in self.tracklets]
        ious = compute_ious(bboxes0, bboxes1, self.bbox_margin)
        observations = [None] * len(bboxes1)

        for a, b in np.array(linear_sum_assignment(-ious)).T:
            if ious[a, b] < self.iou_threshold:
                continue

            prob, bbox0, _ = faces[a]
            bboxes0[a] = None
            observations[b] = bbox0

            xmin, ymin, xmax, ymax = bbox0

            detected = (
                not self.tracklets[b][4]
                and xmin >= self.area_xmin
                and xmax <= self.area_xmax
                and ymin >= self.area_ymin
                and ymax <= self.area_ymax
            )
            if not self.tracklets[b][4] and detected:
                x, P, id, miss, _ = self.tracklets[b]
                self.tracklets[b] = x, P, id, miss, True

            ret.append((prob, xmin, ymin, xmax, ymax, detected, self.tracklets[b][2]))

        # update KF with observed bboxes
        self.update_KF(observations)

        # Add new bboxes
        for i, bbox in enumerate(bboxes0):
            if bbox:
                x = np.zeros(7)
                x[:4] = bbox_to_z(bbox)

                prob = faces[i][0]
                xmin, ymin, xmax, ymax = bbox
                detected = (
                    xmin >= self.area_xmin
                    and xmax <= self.area_xmax
                    and ymin >= self.area_ymin
                    and ymax <= self.area_ymax
                )
                self.tracklets.append((x, P0, self.nextid, 0, detected))
                ret.append((prob, xmin, ymin, xmax, ymax, detected, self.nextid))

                self.nextid += 1

        return ret
