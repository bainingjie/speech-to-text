import numpy as np
import os
import onnxruntime
from concurrent.futures import ThreadPoolExecutor

current_dir = os.path.dirname(os.path.abspath(__file__))

class Vad:
    def __init__(self, threshold: float = 0.1, batch_size: int = 10):
        model_path = os.path.join(current_dir, "assets", "silero_vad.onnx")

        options = onnxruntime.SessionOptions()
        options.log_severity_level = 4
        options.enable_cpu_mem_arena = True
        options.intra_op_num_threads = os.cpu_count()

        self.inference_session = onnxruntime.InferenceSession(
            model_path, sess_options=options
        )
        self.SAMPLING_RATE = 16000
        self.threshold = threshold
        self.h = np.zeros((2, 1, 64), dtype=np.float32)
        self.c = np.zeros((2, 1, 64), dtype=np.float32)
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor()

    def is_speech_batch(self, audio_data_list: list) -> list:
        input_data = {
            "input": np.vstack([data.reshape(1, -1) for data in audio_data_list]),
            "sr": np.array([self.SAMPLING_RATE] * len(audio_data_list), dtype=np.int64),
            "h": self.h,
            "c": self.c,
        }
        out, h, c = self.inference_session.run(None, input_data)
        self.h, self.c = h, c
        return out > self.threshold

    def is_speech(self, audio_data: np.ndarray) -> bool:
        future = self.executor.submit(self.is_speech_batch, [audio_data])
        return future.result()[0]