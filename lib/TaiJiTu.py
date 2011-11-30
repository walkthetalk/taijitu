# coding=utf-8
import math
import cairo
import wx

class TaiJiTu():
	def __init__(self,parent,width,height):
		self.__parent = parent

		self.__width = width
		self.__height = height

		# 准备surface和ctx
		self.__surface = cairo.ImageSurface(
			cairo.FORMAT_ARGB32, width, height)
		
		self.__ctx = cairo.Context(self.__surface)
		self.__ctx.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
		self.__ctx.scale(self.__width, self.__height)
		self.__ctx.translate(0.5, 0.5)

		self.__blackPat = cairo.SolidPattern(0,0,0)
		self.__whitePat = cairo.SolidPattern(1,1,1)

		self.__bagua = dict()
		self.__bagua["qian"] = (-math.pi / 2, (True, True, True))
		self.__bagua["xu"] = (-math.pi / 4, (True, True, False))
		self.__bagua["kan"] = (0, (False, True, False))
		self.__bagua["gen"] = (math.pi / 4, (True, False, False))
		self.__bagua["kun"] = (math.pi / 2, (False, False, False))
		self.__bagua["zhen"] = (3 * math.pi / 4, (False, False, True))
		self.__bagua["li"] = (math.pi, (True, False, True))
		self.__bagua["dui"] = (5 * math.pi / 4, (False, True, True))

	def Draw(self):
		self.DrawHalfCircle(self.__ctx,
			self.__whitePat, self.__blackPat, 0)
		self.DrawHalfCircle(self.__ctx,
			self.__blackPat, self.__whitePat, math.pi)

		for item in self.__bagua:
			self.DrawBaGua(self.__ctx, self.__bagua[item])

	def DrawHalfCircle(self, ctx, pat1, pat2, angle):
		ctx.save()
		ctx.scale(0.5, 0.5)
		ctx.rotate(angle)

		ctx.new_path()
		#ctx.new_sub_path()
		ctx.arc(0, 0, 0.5, -math.pi / 2, math.pi / 2)
		#ctx.new_sub_path()
		ctx.arc_negative(0, 0.25, 0.25, math.pi / 2, -math.pi / 2)
		#ctx.new_sub_path()
		ctx.arc(0, -0.25, 0.25, math.pi / 2, -math.pi / 2)

		ctx.set_source(pat1)
		ctx.fill()

		ctx.new_path()
		ctx.arc(0, -0.25, 0.5/6, -math.pi * 2, 0)
		ctx.set_source(pat2)
		ctx.fill()

		ctx.restore()
	def DrawBaGua(self, ctx, singleGua):
		(angle, guaxiang) = singleGua
		ctx.save()

		ctx.rotate(angle)

		ctx.new_path()

		ctx.set_line_width(0.025)
		ctx.set_source(self.__blackPat)
		len_halfyang = 0.08
		len_halfblank = 0.02
		for i, yao in enumerate(guaxiang):
			ctx.save()
			ctx.translate(0.35 + i * 0.05, 0)
			if yao: # 阳爻
				ctx.move_to(0, -len_halfyang)
				ctx.line_to(0, len_halfyang)
			else:	# 阴爻
				ctx.move_to(0, -len_halfyang)
				ctx.line_to(0, -len_halfblank)
				ctx.move_to(0, len_halfblank)
				ctx.line_to(0, len_halfyang)
			ctx.restore()

		ctx.stroke()

		ctx.restore()
	def ToWxBitmap(self):
		self.Draw()

		format = self.__surface.get_format()
		if format not in [cairo.FORMAT_ARGB32, cairo.FORMAT_RGB24]:
			raise TypeError("Unsupported format")

		width  = self.__surface.get_width()
		height = self.__surface.get_height()
		stride = self.__surface.get_stride()
		data   = self.__surface.get_data()
		if format == cairo.FORMAT_ARGB32:
			fmt = wx.BitmapBufferFormat_ARGB32
		else:
			fmt = wx.BitmapBufferFormat_RGB32

		bmp = wx.EmptyBitmap(width, height, 32)
		bmp.CopyFromBuffer(data, fmt, stride)
		return bmp

