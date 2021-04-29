#from ai_service.service import AIService
from backend.handlers import base


class AIDetectHandler(base.AsyncHandler):
    """ ai detect for test """
    pass
    """
    def do_post(self, data):

        image_file_path = data.get("image")
        detect_type = int(data.get("type", 0))
        if not image_file_path:
            return self.failed(601, "not found image")
        if not detect_type:
            return self.failed(602, "not found detect_type")

        if detect_type in [1, 8]:
            if detect_type == 1:
                port = "50052"
            else:
                port = "50051"
            ai_service = AIService(host="edgegw.iotedge", port=port)
            results = ai_service.ai_detect(image_file_path, num=detect_type)
            return self.success(results)
        if detect_type == 9:
            results = pre_dataprocess(image_file_path)
            return self.success(results)
        return self.failed("603", "detect_type is bad")
    """