# Copyright 2022 The MediaPipe Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""MediaPipe gesture recognizer task."""

import ctypes
import dataclasses
import logging
from typing import Callable

from mediapipe.tasks.python.components.processors import classifier_options
from mediapipe.tasks.python.components.processors import classifier_options_c
from mediapipe.tasks.python.core import base_options as base_options_module
from mediapipe.tasks.python.core import base_options_c
from mediapipe.tasks.python.core import mediapipe_c_bindings
from mediapipe.tasks.python.core import serial_dispatcher
from mediapipe.tasks.python.core.optional_dependencies import doc_controls
from mediapipe.tasks.python.vision import gesture_recognizer_result as gesture_recognizer_result_module
# C-bindings
from mediapipe.tasks.python.vision import gesture_recognizer_result_c
from mediapipe.tasks.python.vision.core import base_vision_task_api
from mediapipe.tasks.python.vision.core import image as image_lib
from mediapipe.tasks.python.vision.core import image_processing_options as image_processing_options_lib
from mediapipe.tasks.python.vision.core import image_processing_options_c
from mediapipe.tasks.python.vision.core import vision_task_running_mode as running_mode_module

_BaseOptions = base_options_module.BaseOptions
_ClassifierOptions = classifier_options.ClassifierOptions
_RunningMode = running_mode_module.VisionTaskRunningMode
_ImageProcessingOptions = image_processing_options_lib.ImageProcessingOptions
_GestureRecognizerResult = (
    gesture_recognizer_result_module.GestureRecognizerResult
)
_CFunction = mediapipe_c_bindings.CFunction


class GestureRecognizerOptionsC(ctypes.Structure):
  _fields_ = [
      ('base_options', base_options_c.BaseOptionsC),
      ('running_mode', ctypes.c_int),
      ('num_hands', ctypes.c_int),
      ('min_hand_detection_confidence', ctypes.c_float),
      ('min_hand_presence_confidence', ctypes.c_float),
      ('min_tracking_confidence', ctypes.c_float),
      (
          'canned_gestures_classifier_options',
          classifier_options_c.ClassifierOptionsC,
      ),
      (
          'custom_gestures_classifier_options',
          classifier_options_c.ClassifierOptionsC,
      ),
      (
          'result_callback',
          ctypes.CFUNCTYPE(
              None,
              ctypes.POINTER(
                  gesture_recognizer_result_c.GestureRecognizerResultC
              ),
              ctypes.c_void_p,
              ctypes.c_int64,
              ctypes.c_char_p,
          ),
      ),
  ]


_CTYPES_SIGNATURES = (
    _CFunction(
        'gesture_recognizer_create',
        [
            ctypes.POINTER(GestureRecognizerOptionsC),
            ctypes.POINTER(ctypes.c_char_p),
        ],
        ctypes.c_void_p,
    ),
    _CFunction(
        'gesture_recognizer_recognize_image',
        [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(image_processing_options_c.ImageProcessingOptionsC),
            ctypes.POINTER(
                gesture_recognizer_result_c.GestureRecognizerResultC
            ),
            ctypes.POINTER(ctypes.c_char_p),
        ],
        ctypes.c_int,
    ),
    _CFunction(
        'gesture_recognizer_recognize_for_video',
        [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(image_processing_options_c.ImageProcessingOptionsC),
            ctypes.c_int64,
            ctypes.POINTER(
                gesture_recognizer_result_c.GestureRecognizerResultC
            ),
            ctypes.POINTER(ctypes.c_char_p),
        ],
        ctypes.c_int,
    ),
    _CFunction(
        'gesture_recognizer_recognize_async',
        [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(image_processing_options_c.ImageProcessingOptionsC),
            ctypes.c_int64,
            ctypes.POINTER(ctypes.c_char_p),
        ],
        ctypes.c_int,
    ),
    _CFunction(
        'gesture_recognizer_close_result',
        [ctypes.POINTER(gesture_recognizer_result_c.GestureRecognizerResultC)],
        None,
    ),
    _CFunction(
        'gesture_recognizer_close',
        [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_char_p),
        ],
        ctypes.c_int,
    ),
)


@dataclasses.dataclass
class GestureRecognizerOptions:
  """Options for the gesture recognizer task.

  Attributes:
    base_options: Base options for the hand gesture recognizer task.
    running_mode: The running mode of the task. Default to the image mode.
      Gesture recognizer task has three running modes: 1) The image mode for
      recognizing hand gestures on single image inputs. 2) The video mode for
      recognizing hand gestures on the decoded frames of a video. 3) The live
      stream mode for recognizing hand gestures on a live stream of input data,
      such as from camera.
    num_hands: The maximum number of hands can be detected by the recognizer.
    min_hand_detection_confidence: The minimum confidence score for the hand
      detection to be considered successful.
    min_hand_presence_confidence: The minimum confidence score of hand presence
      score in the hand landmark detection.
    min_tracking_confidence: The minimum confidence score for the hand tracking
      to be considered successful.
    canned_gesture_classifier_options: Options for configuring the canned
      gestures classifier, such as score threshold, allow list and deny list of
      gestures. The categories for canned gesture classifiers are: ["None",
      "Closed_Fist", "Open_Palm", "Pointing_Up", "Thumb_Down", "Thumb_Up",
      "Victory", "ILoveYou"]. Note this option is subject to change.
    custom_gesture_classifier_options: Options for configuring the custom
      gestures classifier, such as score threshold, allow list and deny list of
      gestures. Note this option is subject to change.
    result_callback: The user-defined result callback for processing live stream
      data. The result callback should only be specified when the running mode
      is set to the live stream mode.
  """

  base_options: _BaseOptions
  running_mode: _RunningMode = _RunningMode.IMAGE
  num_hands: int = 1
  min_hand_detection_confidence: float = 0.5
  min_hand_presence_confidence: float = 0.5
  min_tracking_confidence: float = 0.5
  canned_gesture_classifier_options: _ClassifierOptions = dataclasses.field(
      default_factory=_ClassifierOptions
  )
  custom_gesture_classifier_options: _ClassifierOptions = dataclasses.field(
      default_factory=_ClassifierOptions
  )
  result_callback: (
      Callable[[_GestureRecognizerResult, image_lib.Image, int], None] | None
  ) = None

  _result_callback_c: (
      Callable[
          [
              gesture_recognizer_result_c.GestureRecognizerResultC,
              ctypes.c_void_p,
              int,
              str,
          ],
          None,
      ]
      | None
  ) = None

  @doc_controls.do_not_generate_docs
  def to_ctypes(self) -> GestureRecognizerOptionsC:
    """Generates a GestureRecognizerOptionsC ctypes struct."""
    if self._result_callback_c is None:
      result_callback_fn = ctypes.CFUNCTYPE(
          None,
          ctypes.POINTER(gesture_recognizer_result_c.GestureRecognizerResultC),
          ctypes.c_void_p,
          ctypes.c_int64,
          ctypes.c_char_p,
      )

      @result_callback_fn
      def c_callback(result, image, timestamp_ms, error_msg):
        if self.result_callback:
          if error_msg:
            logging.error('Gesture recognizer error: %s', error_msg.decode())
            return
          py_result = _GestureRecognizerResult.from_ctypes(result.contents)
          py_image = image_lib.Image.create_from_ctypes(image)
          self.result_callback(py_result, py_image, timestamp_ms)

      self._result_callback_c = c_callback

    return GestureRecognizerOptionsC(
        base_options=self.base_options.to_ctypes(),
        running_mode=self.running_mode.ctype,
        num_hands=self.num_hands,
        min_hand_detection_confidence=self.min_hand_detection_confidence,
        min_hand_presence_confidence=self.min_hand_presence_confidence,
        min_tracking_confidence=self.min_tracking_confidence,
        canned_gestures_classifier_options=classifier_options_c.convert_to_classifier_options_c(
            self.canned_gesture_classifier_options
        ),
        custom_gestures_classifier_options=classifier_options_c.convert_to_classifier_options_c(
            self.custom_gesture_classifier_options
        ),
        result_callback=self._result_callback_c,
    )


class GestureRecognizer:
  """Class that performs gesture recognition on images."""

  _lib: serial_dispatcher.SerialDispatcher
  _handle: ctypes.c_void_p

  def __init__(
      self, lib: serial_dispatcher.SerialDispatcher, handle: ctypes.c_void_p
  ):
    self._lib = lib
    self._handle = handle

  @classmethod
  def create_from_model_path(cls, model_path: str) -> 'GestureRecognizer':
    """Creates an `GestureRecognizer` object from a TensorFlow Lite model and the default `GestureRecognizerOptions`.

    Note that the created `GestureRecognizer` instance is in image mode, for
    recognizing hand gestures on single image inputs.

    Args:
      model_path: Path to the model.

    Returns:
      `GestureRecognizer` object that's created from the model file and the
      default `GestureRecognizerOptions`.

    Raises:
      ValueError: If failed to create `GestureRecognizer` object from the
        provided file such as invalid file path.
      RuntimeError: If other types of error occurred.
    """
    base_options = _BaseOptions(model_asset_path=model_path)
    options = GestureRecognizerOptions(
        base_options=base_options, running_mode=_RunningMode.IMAGE
    )
    return cls.create_from_options(options)

  @classmethod
  def create_from_options(
      cls, options: GestureRecognizerOptions
  ) -> 'GestureRecognizer':
    """Creates the `GestureRecognizer` object from gesture recognizer options.

    Args:
      options: Options for the gesture recognizer task.

    Returns:
      `GestureRecognizer` object that's created from `options`.

    Raises:
      ValueError: If failed to create `GestureRecognizer` object from
        `GestureRecognizerOptions` such as missing the model.
      RuntimeError: If other types of error occurred.
    """
    base_vision_task_api.validate_running_mode(
        options.running_mode, options.result_callback
    )

    lib = mediapipe_c_bindings.load_shared_library(_CTYPES_SIGNATURES)

    options_c = options.to_ctypes()
    error_msg_ptr = ctypes.c_char_p()
    recognizer_handle = lib.gesture_recognizer_create(
        ctypes.byref(options_c), ctypes.byref(error_msg_ptr)
    )

    if not recognizer_handle:
      if error_msg_ptr.value is not None:
        error_message = error_msg_ptr.value.decode('utf-8')
        raise RuntimeError(error_message)
      else:
        raise RuntimeError('Failed to create GestureRecognizer object.')

    return cls(lib=lib, handle=recognizer_handle)

  def recognize(
      self,
      image: image_lib.Image,
      image_processing_options: _ImageProcessingOptions | None = None,
  ) -> _GestureRecognizerResult:
    """Performs hand gesture recognition on the given image.

    Only use this method when the GestureRecognizer is created with the image
    running mode.

    The image can be of any size with format RGB or RGBA.
    TODO: Describes how the input image will be preprocessed after the yuv
    support is implemented.

    Args:
      image: MediaPipe Image.
      image_processing_options: Options for image processing.

    Returns:
      The hand gesture recognition results.

    Raises:
      ValueError: If any of the input arguments is invalid.
      RuntimeError: If gesture recognition failed to run.
    """
    c_image = image._image_ptr  # pylint: disable=protected-access
    c_result = gesture_recognizer_result_c.GestureRecognizerResultC()
    error_msg = ctypes.c_char_p()
    options_c = (
        ctypes.byref(image_processing_options.to_ctypes())
        if image_processing_options
        else None
    )
    status = self._lib.gesture_recognizer_recognize_image(
        self._handle,
        c_image,
        options_c,
        ctypes.byref(c_result),
        ctypes.byref(error_msg),
    )

    mediapipe_c_bindings.handle_return_code(
        status, 'Failed to recognize gesture', error_msg
    )

    result = _GestureRecognizerResult.from_ctypes(c_result)
    self._lib.gesture_recognizer_close_result(ctypes.byref(c_result))
    return result

  def recognize_for_video(
      self,
      image: image_lib.Image,
      timestamp_ms: int,
      image_processing_options: _ImageProcessingOptions | None = None,
  ) -> _GestureRecognizerResult:
    """Performs gesture recognition on the provided video frame.

    Only use this method when the GestureRecognizer is created with the video
    running mode.

    Only use this method when the GestureRecognizer is created with the video
    running mode. It's required to provide the video frame's timestamp (in
    milliseconds) along with the video frame. The input timestamps should be
    monotonically increasing for adjacent calls of this method.

    Args:
      image: MediaPipe Image.
      timestamp_ms: The timestamp of the input video frame in milliseconds.
      image_processing_options: Options for image processing.

    Returns:
      The hand gesture recognition results.

    Raises:
      ValueError: If any of the input arguments is invalid.
      RuntimeError: If gesture recognition failed to run.
    """
    c_image = image._image_ptr  # pylint: disable=protected-access
    c_result = gesture_recognizer_result_c.GestureRecognizerResultC()
    error_msg = ctypes.c_char_p()
    options_c = (
        ctypes.byref(image_processing_options.to_ctypes())
        if image_processing_options
        else None
    )
    status = self._lib.gesture_recognizer_recognize_for_video(
        self._handle,
        c_image,
        options_c,
        timestamp_ms,
        ctypes.byref(c_result),
        ctypes.byref(error_msg),
    )

    mediapipe_c_bindings.handle_return_code(
        status, 'Failed to recognize gesture for video', error_msg
    )

    result = _GestureRecognizerResult.from_ctypes(c_result)
    self._lib.gesture_recognizer_close_result(ctypes.byref(c_result))
    return result

  def recognize_async(
      self,
      image: image_lib.Image,
      timestamp_ms: int,
      image_processing_options: _ImageProcessingOptions | None = None,
  ) -> None:
    """Sends live image data to perform gesture recognition.

    The results will be available via the "result_callback" provided in the
    GestureRecognizerOptions. Only use this method when the GestureRecognizer
    is created with the live stream running mode.

    Only use this method when the GestureRecognizer is created with the live
    stream running mode. The input timestamps should be monotonically increasing
    for adjacent calls of this method. This method will return immediately after
    the input image is accepted. The results will be available via the
    `result_callback` provided in the `GestureRecognizerOptions`. The
    `recognize_async` method is designed to process live stream data such as
    camera input. To lower the overall latency, gesture recognizer may drop the
    input images if needed. In other words, it's not guaranteed to have output
    per input image.

    The `result_callback` provides:
      - The hand gesture recognition results.
      - The input image that the gesture recognizer runs on.
      - The input timestamp in milliseconds.

    Args:
      image: MediaPipe Image.
      timestamp_ms: The timestamp of the input image in milliseconds.
      image_processing_options: Options for image processing.

    Raises:
      ValueError: If the current input timestamp is smaller than what the
      gesture recognizer has already processed.
    """
    c_image = image._image_ptr  # pylint: disable=protected-access
    error_msg = ctypes.c_char_p()
    options_c = (
        ctypes.byref(image_processing_options.to_ctypes())
        if image_processing_options
        else None
    )
    status = self._lib.gesture_recognizer_recognize_async(
        self._handle,
        c_image,
        options_c,
        timestamp_ms,
        ctypes.byref(error_msg),
    )

    mediapipe_c_bindings.handle_return_code(
        status, 'Failed to recognize gesture asynchronously', error_msg
    )

  def close(self):
    """Closes GestureRecognizer."""
    if self._handle:
      error_msg = ctypes.c_char_p()
      status = self._lib.gesture_recognizer_close(
          self._handle, ctypes.byref(error_msg)
      )
      mediapipe_c_bindings.handle_return_code(
          status, 'Failed to close GestureRecognizer', error_msg
      )
    self._handle = None
    self._lib.close()

  def __enter__(self):
    """Returns `self` upon entering the runtime context."""
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    """Closes GestureRecognizers and exits the context manager.

    Args:
      exc_type: The exception type that caused the context manager to exit.
      exc_value: The exception value that caused the context manager to exit.
      traceback: The exception traceback that caused the context manager to
        exit.

    Raises:
      RuntimeError: If the MediaPipe Gesture Recognizer task failed to
      close.
    """
    self.close()
