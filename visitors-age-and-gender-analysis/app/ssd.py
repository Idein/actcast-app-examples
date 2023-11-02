import math
import numpy as np

SSD_WIDTH = 320
SSD_HEIGHT = 240

NUM_LABELS = 1 + 1


class UltraLightFastGenericFaceDetector1MB_QDNN(object):
    def __init__(self, model, area_min, area_max, threshold=0.7, iou_threshold=0.3):
        super(UltraLightFastGenericFaceDetector1MB_QDNN, self).__init__()

        self.model = model
        self.area_min = area_min
        self.area_max = area_max
        self.threshold = threshold
        self.iou_threshold = iou_threshold

    def run(self, image):
        return self.model.SSD(image)

    def run_detect(self, image):
        return self.detect(self.run(image))

    def detect(self, box_scores):
        # params
        conf_threshold = math.log(1 / self.threshold - 1)
        center_variance = 0.1
        size_variance = 0.2
        min_boxes = [
            [[10 / 320, 7.5 / 240], [16 / 320, 12 / 240], [22.63 / 320, 16.97 / 240]],
            [[32 / 320, 24 / 240], [64 / 320, 48 / 240], [90.51 / 320, 67.88 / 240]],
            [
                [128 / 320, 96 / 240],
                [192 / 320, 144 / 240],
                [247.87 / 320, 185.90 / 240],
                [320 / 320, 240 / 240],
            ],
        ]
        feature_map_w_h_list = [[40, 20, 10], [30, 15, 8]]

        def rect_intersection(a, b):
            ax_min, ay_min, ax_max, ay_max = a
            bx_min, by_min, bx_max, by_max = b

            l = max(ax_min, bx_min)
            r = min(ax_max, bx_max)
            u = max(ay_min, by_min)
            d = min(ay_max, by_max)

            w = max(r - l, 0)
            h = max(d - u, 0)

            return w * h

        def rect_union(a, b):
            ax_min, ay_min, ax_max, ay_max = a
            bx_min, by_min, bx_max, by_max = b

            aw = ax_max - ax_min
            ah = ay_max - ay_min
            bw = bx_max - bx_min
            bh = by_max - by_min

            return aw * ah + bw * bh - rect_intersection(a, b)

        candidates = list()
        for layer, (bboxes, confs) in enumerate(zip(box_scores[:3], box_scores[3:])):
            min_box = min_boxes[layer]
            feature_map_w = feature_map_w_h_list[0][layer]
            feature_map_h = feature_map_w_h_list[1][layer]
            bboxes = bboxes.transpose((0, 2, 3, 1))
            bboxes = bboxes.reshape(bboxes.shape[:3] + (bboxes.shape[3] // 4, 4))
            confs = confs.transpose((0, 2, 3, 1))
            confs = confs.reshape(confs.shape[:3] + (confs.shape[3] // 2, 2))
            # NB: calculation of confidence score is specialized for 1-class model.
            confs[:, :, :, :, 1] -= confs[:, :, :, :, 0]
            ixs = np.where(-confs[:, :, :, :, 1] < conf_threshold)
            for ix in list(np.array(ixs).T):
                conf = 1 / (1 + math.exp(-confs[tuple(ix) + (1,)]))
                [_, y, x, box_spec_ix] = ix
                ycenter_a = (y + 0.5) / feature_map_h
                xcenter_a = (x + 0.5) / feature_map_w
                height_a = min_box[box_spec_ix][1]
                width_a = min_box[box_spec_ix][0]
                [tx, ty, tw, th] = bboxes[tuple(ix)]
                ycenter = ty * center_variance * height_a + ycenter_a
                xcenter = tx * center_variance * width_a + xcenter_a
                height = math.exp(th * size_variance) * height_a
                width = math.exp(tw * size_variance) * width_a
                if width * height < self.area_min or width * height > self.area_max:
                    continue
                y_min = max(ycenter - height / 2.0, 0.0)
                y_max = min(ycenter + height / 2.0, 1.0)
                x_min = max(xcenter - width / 2.0, 0.0)
                x_max = min(xcenter + width / 2.0, 1.0)
                candidates.append((conf, [x_min, y_min, x_max, y_max], 1))

        nmsed_candidates = []
        candidates.sort(reverse=True)
        while len(candidates) > 0:
            a = candidates.pop(0)
            nmsed_candidates.append(a)
            _, a_rect, a_c = a

            def nms(b):
                _, b_rect, b_c = b
                if a_c != b_c:
                    return True
                i = rect_intersection(a_rect, b_rect)
                u = rect_union(a_rect, b_rect)
                return i / u <= self.iou_threshold

            candidates = list(filter(nms, candidates))
        candidates = nmsed_candidates

        return candidates
