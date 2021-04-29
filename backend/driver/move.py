import cv2
import numpy as np

class Model():
    def __init__(self):
        self.history = 100
        self.cv_detector = cv2.createBackgroundSubtractorMOG2(history=self.history, varThreshold=100, detectShadows=True)
        self.previous_list = []

    def pre_dataprocess(self, image):
        original_image = image.copy()
        h_org, w_org, c_org = original_image.shape
        h_target, w_target = (480, 640)

        resize_ratio = min(1.0 * w_target / w_org, 1.0 * h_target / h_org)
        resize_w = int(resize_ratio * w_org)
        resize_h = int(resize_ratio * h_org)
        resized_image = cv2.resize(original_image, (resize_w, resize_h))

        image_paded = np.full((h_target, w_target, 3), 0.0)
        dw = int((w_target - resize_w) / 2)
        dh = int((h_target - resize_h) / 2)
        image_paded[dh:resize_h+dh, dw:resize_w+dw, :] = resized_image

        return image_paded, original_image.shape

    def post_dataprocess(self, bboxes, original_image_shape):
        (h_org, w_org, c_org) = original_image_shape
        input_w, input_h = (640, 480)
        resize_ratio = min(1.0 * input_w / w_org, 1.0 * input_h / h_org)
        dw = (input_w - resize_ratio * w_org) / 2
        dh = (input_h - resize_ratio * h_org) / 2

        results = []
        for (ymin, ymax, xmin, xmax, _) in bboxes:
            new_xmin = 1.0 * (xmin - dw) / resize_ratio
            new_ymin = 1.0 * (ymin - dh) / resize_ratio
            new_xmax = 1.0 * (xmax - dw) / resize_ratio
            new_ymax = 1.0 * (ymax - dh) / resize_ratio
            results.append(['movement', '0.666', new_xmin, new_ymin, new_xmax, new_ymax])

        return results

    def compute(self, path):
        image = cv2.imread(path)
        frame, original_image_shape = self.pre_dataprocess(image)
        frame_motion = frame.copy()
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(frame.shape[1] * 0.01), int(frame.shape[0] * 0.01)))
        location_list = self.img_to_block(480, 640)

        fgmask = self.cv_detector.apply(frame_motion)
        draw1 = cv2.threshold(fgmask, 25, 255, cv2.THRESH_BINARY)[1]
        draw1 = cv2.morphologyEx(draw1, cv2.MORPH_OPEN, kernel)
        motion_blocks = self.motion_extension(draw1, location_list)
        mm = np.zeros(frame_motion.shape).astype(np.uint8)
        for y, x, h, w in motion_blocks:
            cv2.rectangle(mm, (x, y), (x + w, y + h), (255, 255, 255), -1)
        mm = cv2.cvtColor(mm, cv2.COLOR_BGR2GRAY)

        countours = cv2.findContours(mm.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(countours) == 3:
            _, contours_m, hierarchy_m = countours[0], countours[1], countours[2]
        elif len(countours) == 2:
            contours_m, hierarchy_m = countours[0], countours[1]

        bboxes = []
        for c in contours_m:
            if cv2.contourArea(c) < (frame.shape[0] * 0.02) * (frame.shape[1] * 0.02):
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            x1, x2 = x, x + w
            y1, y2 = y, y + h
            bboxes.append([y1, y2, x1, x2, (y2 - y1) * (x2 - x1)])

        if len(bboxes) > 0:
            bboxes = np.array(bboxes)
            bboxes = self.nms(bboxes, 0.5)

        results = self.post_dataprocess(bboxes, original_image_shape)
        return results

    def img_to_block(self, rows, cols):
        result = []
        block_size = int(0.05 * min(rows, cols))
        for c in range(0, block_size * (cols // block_size), block_size):
            for r in range(0, block_size * (rows // block_size), block_size):
                box = (r, c, block_size, block_size)
                result.append(box)
        return result

    def motion_extension(self, dilated, location_list):
        block_size = int(0.05 * min(dilated.shape[0], dilated.shape[1]))
        int_diff = cv2.integral(dilated)

        result = list()
        for pt in iter(location_list):
            xx, yy, _bz, _bz = pt
            t11 = int_diff[xx, yy]
            t22 = int_diff[xx + block_size, yy + block_size]
            t12 = int_diff[xx, yy + block_size]
            t21 = int_diff[xx + block_size, yy]
            block_diff = t11 + t22 - t12 - t21
            if block_diff > 0:
                result.append((xx, yy, block_size, block_size))
        return result

    def nms(self, bbox, thresh=0.5):
        if bbox.shape[0] == 0:
            return bbox
        # bbox = [[x, y, w, h, score]]
        x1 = bbox[:, 0]
        y1 = bbox[:, 1]
        x2 = bbox[:, 2]
        y2 = bbox[:, 3]
        score = bbox[:, 4]
        # sort score by decreasing order
        order = score.argsort()[::-1]
        # areas for every boundary box
        areas = (x2 - x1) * (y2 - y1)

        keep = []
        while order.shape[0] > 0:
            # bounding box with highest score
            i = order[0]
            keep.append(i)
            # IOU = intersection / union
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            # intersection
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            intersection = w * h
            # union
            union = areas[i] + areas[order[1:]] - intersection
            IOU = intersection / union
            # print(IOU)

            inds = np.where(IOU <= thresh)
            # order = order[inds[0] + 1]
            order = np.delete(order, inds[0])
            order = order[1:]

        return bbox[keep].astype(np.int32)