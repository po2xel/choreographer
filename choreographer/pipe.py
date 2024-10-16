import os
import sys
import json
import platform
import warnings

with_block = bool(sys.version_info[:3] >= (3, 12) or platform.system() != "Windows")
class BlockWarning(UserWarning):
    pass

# TODO: don't know about this
# TODO: use has_attr instead of np.integer, you'll be fine
class NumpyEncoder(json.JSONEncoder):
    """Special json encoder for numpy types"""

    def default(self, obj):
        if (
            hasattr(obj, "dtype")
            and obj.dtype.kind == "i"
            and obj.shape == ()
        ):
            return int(obj)
        elif (
            hasattr(obj, "dtype")
            and obj.dtype.kind == "f"
            and obj.shape == ()
        ):
            return float(obj)
        elif hasattr(obj, "dtype") and obj.shape != ():
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class PipeClosedError(IOError):
    pass

class Pipe:
    def __init__(self, debug=False, cls=NumpyEncoder):
        self.read_from_chromium, self.write_from_chromium = list(os.pipe())
        self.read_to_chromium, self.write_to_chromium = list(os.pipe())
        self.debug = debug
        self.cls=cls

    def write_json(self, obj, debug=None):
        if not debug: debug = self.debug
        if debug:
            print("write_json:", file=sys.stderr)
        message = json.dumps(obj, ensure_ascii=False, cls=self.cls)
        encoded_message = message.encode("utf-8") + b"\0"
        if debug:
            print(f"write_json: {message}", file=sys.stderr)
            # windows may print weird characters if we set utf-8 instead of utf-16
            # check this TODO
        os.write(self.write_to_chromium, encoded_message)

    def read_jsons(self, blocking=True, debug=None):
        if not with_block and not blocking:
            warnings.warn("Windows python version < 3.12 does not support non-blocking", BlockWarning)
        if not debug:
            debug = self.debug
        if debug:
            print(f"read_jsons ({'blocking' if blocking else 'not blocking'}):", file=sys.stderr)
        jsons = []
        try:
            if with_block: os.set_blocking(self.read_from_chromium, blocking)
        except OSError as e:
            raise PipeClosedError() from e
        try:
            raw_buffer = None # if we fail in read, we already defined
            raw_buffer = os.read(
                self.read_from_chromium, 10000
            )  # 10MB buffer, nbd, doesn't matter w/ this
            if not raw_buffer or raw_buffer == b'{bye}\n':
                # we seem to need {bye} even if chrome closes NOTE
                if debug: print("read_jsons pipe was closed, raising", file=sys.stderr)
                raise PipeClosedError()
            while raw_buffer[-1] != 0:
                # still not great, return what you have
                if with_block: os.set_blocking(self.read_from_chromium, True)
                raw_buffer += os.read(self.read_from_chromium, 10000)
        except BlockingIOError:
            if debug:
                print("read_jsons: BlockingIOError caught.", file=sys.stderr)
            return jsons
        except OSError as e:
            if debug:
                print(f"caught OSError in read() {str(e)}", file=sys.stderr)
            if not raw_buffer or raw_buffer == b'{bye}\n':
                raise PipeClosedError()
            # TODO this could be hard to test as it is a real OS corner case
            # but possibly raw_buffer is partial
            # and we don't check for partials
        decoded_buffer = raw_buffer.decode("utf-8")
        if debug:
            print(decoded_buffer, file=sys.stderr)
        for raw_message in decoded_buffer.split("\0"):
            if raw_message:
                try:
                    jsons.append(json.loads(raw_message))
                except BaseException as e:
                    if debug:
                        print(f"Problem with {raw_message} in json: {e}", file=sys.stderr)
                if debug:
                    # This debug is kinda late but the jsons package helps with decoding, since JSON optionally
                    # allows escaping unicode characters, which chrome does (oof)
                    print(f"read_jsons: {jsons[-1]}", file=sys.stderr)
        return jsons

    def _unblock_fd(self, fd):
        try:
            if with_block: os.set_blocking(fd, False)
        except BaseException as e:
            if self.debug:
                print(f"Expected error unblocking {str(fd)}: {str(e)}", file=sys.stderr)

    def _close_fd(self, fd):
        try:
            os.close(fd)
        except BaseException as e:
            if self.debug:
                print(f"Expected error closing {str(fd)}: {str(e)}", file=sys.stderr)

    def _fake_bye(self):
        self._unblock_fd(self.write_from_chromium)
        try:
            os.write(self.write_from_chromium, b'{bye}\n')
        except BaseException as e:
            if self.debug:
                print(f"Caught expected error in self-wrte bye: {str(e)}", file=sys.stderr)

    def close(self):
        if platform.system() == "Windows":
            self._fake_bye()
        self._unblock_fd(self.write_from_chromium)
        self._unblock_fd(self.read_from_chromium)
        self._unblock_fd(self.write_to_chromium)
        self._unblock_fd(self.read_to_chromium)
        self._close_fd(self.write_to_chromium)
        self._close_fd(self.read_from_chromium)
        self._close_fd(self.write_from_chromium)
        self._close_fd(self.read_to_chromium)