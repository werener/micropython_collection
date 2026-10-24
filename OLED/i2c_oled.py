from machine import I2C, Pin
import framebuf


class OLED:
    """Interface for interacting with OLED screen via I2C protocol"""

    address: int
    i2c: I2C

    width: int
    height: int

    __buf: bytearray
    fb: framebuf.FrameBuffer

    def __init__(self, i2c: I2C, width=128, height=64, i2c_addr=None):
        if i2c_addr is None:
            devices = i2c.scan()
            if len(devices) == 0:
                raise Exception(f"No devices found at {i2c}")
            if len(devices) > 1:
                raise Exception(
                    f"Found more than one device {i2c}\nSpecify the i2c address of the display\n"
                )
            i2c_addr = devices[0]

        self.buf = bytearray(width * height // 8)
        self.fb = framebuf.FrameBuffer(self.buf, width, height, framebuf.MONO_VLSB)

        self.i2c = i2c
        self.address = i2c_addr

        self.width = width
        self.height = height
        self.max_col = self.width - 1
        self.max_page = self.height // 8 - 1

    def cmd(self, c) -> None:
        """Send command to OLED"""
        self.i2c.writeto(self.address, b"\x00" + c)

    def init(self) -> None:
        """Initialize SSD1306 display"""
        cmds = [
            b"\xae",  # Display off
            b"\xd5\x80",  # Set display clock divide ratio
            b"\xa8\x3f",  # Set multiplex ratio (1 to 64)
            b"\xd3\x00",  # Set display offset
            b"\x40",  # Set start line address
            b"\x8d\x14",  # Enable charge pump
            b"\x20\x00",  # Set memory addressing mode (Horizontal)
            b"\xa1",  # Set segment re-map (column 127 mapped to SEG0)
            b"\xc8",  # Set COM output scan direction
            b"\xda\x12",  # Set COM pins hardware configuration
            b"\x81\xcf",  # Set contrast control
            b"\xd9\xf1",  # Set pre-charge period
            b"\xdb\x40",  # Set VCOMH deselect level
            b"\xa4",  # Entire display ON (resume to RAM)
            b"\xa6",  # Set normal display (not inverse)
            b"\xaf",  # Turn display on
        ]
        for cmd in cmds:
            self.cmd(cmd)

    def update(self) -> None:
        """Push buffer to OLED"""
        self.cmd(bytes([0x21, 0x00, self.max_col]))
        self.cmd(bytes([0x22, 0x00, self.max_page]))

        # Push buffer
        self.i2c.writeto(self.address, b"\x40" + self.buf)

    # ---------------------------
    # - Frame buffer wrappers   -
    # ---------------------------
    def __normalize_coords(self, x: int, y: int) -> tuple[int, int]:
        if x < 0:
            x = self.width + x
        if y < 0:
            y = self.height + y
        return x, y

    def clear(self) -> OLED:
        """Clear buffer"""
        self.fb.fill(0)
        return self

    def fill(self, color: int = 1) -> OLED:
        """Fill the buffer with a color"""
        self.fb.fill(color)
        return self

    def text(self, msg: str, x: int, y: int, color: int = 1) -> OLED:
        """Send text to the buffer"""
        self.fb.text(msg, *self.__normalize_coords(x, y), color)
        return self

    def pixel(self, x: int, y: int, color: int | None = None) -> OLED | int:
        """Send a pixel to the buffer"""
        if color is None:
            return self.fb.pixel(x, y)

        self.fb.pixel(*self.__normalize_coords(x, y), color)
        return self

    def rect(self, x: int, y: int, width: int, height: int, color: int = 1) -> OLED:
        """Send a rectangle outline to the buffer"""
        self.fb.rect(*self.__normalize_coords(x, y), width, height, color)
        return self

    def fill_rect(
        self, x: int, y: int, width: int, heigth: int, color: int = 1
    ) -> OLED:
        """Send a filled rectangle to the buffer"""
        self.fb.fill_rect(*self.__normalize_coords(x, y), width, heigth, color)
        return self

    def line(self, x1: int, y1: int, x2: int, y2: int, color: int = 1) -> OLED:
        """Send a line to the buffer"""
        self.fb.line(x1, y1, x2, y2, color)
        return self

    def hline(self, x: int, y: int, width: int, color: int = 1) -> OLED:
        """Send a horizontal line to the buffer"""
        self.fb.hline(*self.__normalize_coords(x, y), width, color)
        return self

    def vline(self, x: int, y: int, height: int, color: int = 1) -> OLED:
        """Send a vertical line to the buffer"""
        self.fb.vline(*self.__normalize_coords(x, y), height, color)
        return self

    def ellipse(
        self,
        x: int,
        y: int,
        xr: int,
        yr: int,
        color: int,
        fill=False,
        m: int | None = None,
    ) -> OLED:
        """Send an ellipse to the buffer.

        Radii xr and yr define the geometry; equal values cause a circle to be drawn.


        The optional m parameter enables drawing to be restricted to certain quadrants of the ellipse.
        The LS four bits determine which quadrants are to be drawn, with bit 0 specifying Q1, b1 Q2, b2 Q3 and b3 Q4.
        Quadrants are numbered counterclockwise with Q1 being top right.
        """
        self.fb.ellipse(*self.__normalize_coords(x, y), xr, yr, color, fill, m)
        return self
