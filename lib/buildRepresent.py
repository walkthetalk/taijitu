# coding=utf-8
import math
import cairo
import wx
import Queue
import threading

import pyFreeType as pyFF

g_q = Queue.Queue()

def workerth():
	while True:
		item = g_q.get()
		ret = item.exe()
		g_q.task_done()
		#if ret = False:
		#	break

th = threading.Thread(target=workerth)
th.daemon = True
th.start()


# stroke	画线
# fill		填充
class BaseDI():
	def __init__(self, parent):
		self.__parent = parent
		self.__bMotion = False
		self.__bDown = False
	def getParent(self):
		return self.__parent
	def setMotion(self, ismotion):
		self.__bMotion = ismotion
	def getMotion(self):
		return self.__bMotion
	def setDown(self, isDown):
		self.__bDown = isDown
	def getDown(self):
		return self.__bDown
class NodeDrawInfo(BaseDI):
	__fontface = pyFF.create_fontface()
	def __init__(self, parent, ctx, node):
		BaseDI.__init__(self, parent)
		self.__node = node
		# 关联
		self.__node.set_drawinfo(self)

		# 计算
		self.Calc(ctx)

		# path
		ctx.new_path()
		ctx.arc(0,0,1,-math.pi*2, 0)
		self.__path = ctx.copy_path()
		# mpat
		self.__mpat = cairo.RadialGradient(0, 0, 0.8, 0, 0, 1)
		self.__mpat.add_color_stop_rgba (0, 1, 1, 1, 1)
		self.__mpat.add_color_stop_rgba (0.2, 1, 1, 1, 1)
		self.__mpat.add_color_stop_rgba (1, 0.7, 0, 0, 0)
		# pat
		self.__pat = cairo.RadialGradient(0, 0, 0.8, 0, 0, 1)
		self.__pat.add_color_stop_rgba (0, 0.9, 0.9, 0.9, 0.8)
		self.__pat.add_color_stop_rgba (1, 0.7, 0, 0, 0)
		# dpat
		self.__dpat = cairo.RadialGradient(0.1, 0.1, 0.8, 0, 0, 1)
		self.__dpat.add_color_stop_rgba (0, 0.8, 0.8, 0.8, 0.8)
		self.__dpat.add_color_stop_rgba (0.2, 0.8, 0.8, 0.8, 0.8)
		self.__dpat.add_color_stop_rgba (1, 0.7, 0, 0, 0)

		# 编译
		self.__build_progress = -1
	def Calc(self, ctx):
		(self.__cx, self.__cy) = self.getParent().GetCenter(self.__node)
		self.__r = self.getParent().GetFactor()

		# fontface
	def draw(self, ctx):
		pat = self.__pat
		alpha = 0.7
		if self.getMotion():
			if self.getDown():
				pat = self.__dpat
				alpha = 0.9
			else:
				pat = self.__mpat
				alpha = 0.8
		self.drawtotal(ctx, pat, alpha)

	def drawtotal(self, ctx, pat, alpha):
		if self.__build_progress >= 0:
			self.drawBuild(ctx)
		else:
			self.drawBoard(ctx, pat)
		self.drawLabel(ctx, alpha)
	def drawBoard(self, ctx, pat):
		self.Save(ctx)
		ctx.new_path()
		ctx.append_path(self.__path)
		ctx.set_source(pat)
		ctx.fill()
		self.Restore(ctx)
	def drawLabel(self, ctx, alpha):
		self.Save(ctx)
		# 设置字体
		ctx.set_font_face(self.__fontface)
		ctx.set_font_size(0.5)
		# 计算
		label = self.get_label()
		(x, y, width, height, dx, dy) = ctx.text_extents(label)
		ctx.set_source(cairo.SolidPattern(0, 0, 0, alpha))
		ctx.move_to(- width/2, height/2)
		ctx.show_text(label)
		self.Restore(ctx)
	def drawBuild(self, ctx):
		pat = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
		pat.add_color_stop_rgba (0, 0.7, 0, 0, 0)
		pat.add_color_stop_rgba (self.__build_progress%10*0.1,
			0.7, 0, 0, 0.5)
		pat.add_color_stop_rgba (1, 0.7, 0, 0, 0)
		self.drawBoard(ctx, pat)
	def inside(self, ctx, pos):
		self.Save(ctx)
		ctx.new_path()
		ctx.append_path(self.__path)
		self.Restore(ctx)
		ret = ctx.in_fill(pos[0], pos[1])
		return ret
	def get_label(self):
		return self.__node.get_label()
	def get_radius(self):
		return self.__r
	def get_center(self):
		return (self.__cx, self.__cy)

	def prepare4exe(self, dep, state):
		self.__node.prepare4exe(dep, state, g_q)
	def StartBuild(self):
		self.__build_progress = 0
		self.getParent().StartBuildTimer(self)
	def EndBuild(self):
		self.getParent().EndBuildTimer()
		self.__build_progress = -1
	def IncBuildProgress(self):
		self.__build_progress += 1
	def Save(self, ctx):
		ctx.save()
		ctx.translate(self.__cx, self.__cy)
		ctx.scale(self.__r, self.__r)
	def Restore(self, ctx):
		ctx.restore()
class RelationDrawInfo(BaseDI):
	def __init__(self, parent, ctx, noderel):
		BaseDI.__init__(self, parent)

		self.__noderel = noderel
		# 关联
		self.__noderel.set_drawinfo(self)
		# 计算
		self.Calc(ctx)
	def Calc(self, ctx):
		startDI = self.__noderel.getStart().get_drawinfo()
		endDI = self.__noderel.getEnd().get_drawinfo()

		(self.__sx, self.__sy) = startDI.get_center()
		(self.__ex, self.__ey) = endDI.get_center()
		(self.__sr, self.__er) = (startDI.get_radius(),
				endDI.get_radius())

		(self.__dx, self.__dy) = (self.__ex - self.__sx,
					self.__ey - self.__sy)
		self.__l = math.sqrt(math.pow(self.__dx,2)+math.pow(self.__dy,2))

		if (self.__l < (self.__sr + self.__er + 2 * 2)):
			print("dist is too close")
			return

		# path
		factor = self.getParent().GetFactor()
		nodeEdgeSpace = factor/20
		aW = factor/2	# 箭头宽度
		aH = factor/4	# 箭头高度
		angle = math.pi/8 # 角度

		asx = self.__sr + nodeEdgeSpace
		aex = self.__l - self.__er - nodeEdgeSpace # 箭头顶点纵坐标
		axillax = aex - aW*2/3	# 箭腋坐标
		axillay = aH/3
		ctrl1x = (asx + axillax) /2
		ctrl1y = axillay
		ctrl2x = (asx + axillax) *2/ 3
		ctrl2y = axillay
		ctx.new_path()
		ctx.move_to(asx, 0)
		ctx.arc(0,0,asx,0,angle)
		ctx.curve_to(ctrl1x,ctrl1y,
				ctrl2x,ctrl2y,
				axillax, axillay)
		ctx.line_to(aex - aW, aH)
		ctx.line_to(aex, 0)

		ctx.line_to(asx, 0)

		ctx.arc_negative(0,0,asx,0,-angle)
		ctx.curve_to(ctrl1x,-ctrl1y,
				ctrl2x,-ctrl2y,
				axillax,-axillay)
		ctx.line_to(aex - aW, -aH)
		ctx.line_to(aex, 0)

		ctx.close_path()
		self.__path = ctx.copy_path()

		# pat
		self.__pat = cairo.LinearGradient(asx, 0, aex, 0)
		self.__pat.add_color_stop_rgba (0, 0.7, 0, 0, 0.3)
		self.__pat.add_color_stop_rgba (1, 0.3, 0.2, 0.5, 0.3)

		# mpat
		self.__mpat = cairo.LinearGradient(asx, 0, aex, 0)
		self.__mpat.add_color_stop_rgba (0, 0.7, 0, 0, 1)
		self.__mpat.add_color_stop_rgba (1, 0.3, 0.2, 0.5, 1)

		# dpat
		self.__dpat = cairo.LinearGradient(asx, 0, aex, 0)
		self.__dpat.add_color_stop_rgba (0, 0, 0, 0.5, 1)
		self.__dpat.add_color_stop_rgba (1, 0.2, 0.1, 0.4, 1)
	def draw(self, ctx):
		pat = self.__pat
		if self.getMotion():
			if self.getDown():
				pat = self.__dpat
			else:
				pat = self.__mpat
		self.drawTotal(ctx, pat)
	def drawTotal(self, ctx, pat):
		self.drawBoard(ctx, pat)
	def drawBoard(self, ctx, pat):
		self.Save(ctx)
		ctx.new_path()
		ctx.append_path(self.__path)
		ctx.set_source(pat)
		ctx.fill()
		self.Restore(ctx)
	def inside(self, ctx, pos):
		self.Save(ctx)
		ctx.new_path()
		ctx.append_path(self.__path)
		self.Restore(ctx)
		return ctx.in_fill(pos[0], pos[1])
	def get_label(self):
		return self.__noderel.get_key()
	def Save(self, ctx):
		ctx.save()
		ctx.translate(self.__sx, self.__sy)
		ctx.rotate(math.atan2(self.__dy, self.__dx))
	def Restore(self, ctx):
		ctx.restore()

	def prepare4exe(self, dep, state):
		#print("exe relation: %s" % self.get_label())
		return
class StepTree():
	def __init__(self,parent,width,height,nodedict,relationdict):
		self.__parent = parent
		self.__nodedict = nodedict
		self.__relationdict = relationdict

		# 计算行列数目
		xmax = 0
		ymax = 0
		for item in nodedict:
			pos = nodedict[item].get_pos()
			if xmax < pos[0]:
				xmax = pos[0]
			if ymax < pos[1]:
				ymax = pos[1]

		self.__row = int(ymax + 1)
		self.__col = int(xmax + 1)
		# 计算
		self.Calc(width,height)

		self.__eleDI = []
		# 节点
		self.__stepDI = []
		for item in self.__nodedict:
			nodeDI = NodeDrawInfo(self, self.__ctx,
					self.__nodedict[item])
			self.__eleDI.append(nodeDI)
			self.__stepDI.append(nodeDI)
		# 关系
		self.__relsDI = []
		for i in self.__relationdict:
			noderel = self.__relationdict[i]
			relDI = RelationDrawInfo(self, self.__ctx, noderel)
			self.__eleDI.append(relDI)
			self.__relsDI.append(relDI)

		# 鼠标
		self.__eleDI_motion = None
		self.__mousepos = (0,0)
	def Calc(self, width, height):
		self.__gridwidth = float(width) / self.__col
		self.__gridheight = float(height) / self.__row
		self.__width = width
		self.__height = height

		# 准备surface和ctx
		self.__surface = cairo.ImageSurface(
			cairo.FORMAT_ARGB32, width, height)
		self.__ctx = cairo.Context (self.__surface)
	def OnSize(self, width, height):
		# 保证顺序
		self.Calc(width, height)
		for item in self.__stepDI:
			item.Calc(self.__ctx)
		for item in self.__relsDI:
			item.Calc(self.__ctx)
	def GetCenter(self, node):
		pos = node.get_pos()
		cx = float(2 * pos[0] + 1) / 2 * self.__gridwidth
		cy = float(2 * pos[1] + 1) / 2 * self.__gridheight
		return (cx, cy)
	def GetFactor(self):
		return min(self.__gridwidth,self.__gridheight)/2
	def OnMotion(self, x, y):
		self.__mousepos = (x, y)

		old = self.__eleDI_motion
		new = None
		# check
		for item in self.__eleDI:
			if item.inside(self.__ctx, self.__mousepos):
				new = item
				item.setMotion(True)
				break

		self.__eleDI_motion = new

		if new != old:
			if old != None:
				old.setMotion(False)
				old.setDown(False)

		return (new, old)
	def StartBuildTimer(self, nDI):
		self.__parent.StartBuildTimer(nDI)
	def EndBuildTimer(self):
		self.__parent.EndBuildTimer()
	def SetLeftDown(self, down):
		if self.__eleDI_motion != None:
			self.__eleDI_motion.setDown(down)
	def Draw(self):
		ctx = self.__ctx
		# 背景
		self.DrawBG(ctx)
		
		# 网格
		self.DrawGrid(ctx)

		# 元素
		for item in self.__eleDI:
			item.draw(ctx)
	def DrawBG(self, ctx):
		ctx.save()
		ctx.scale(self.__width, self.__height)

		pat = cairo.LinearGradient (0,0,1,1)
		pat.add_color_stop_rgba (0, 1, 1, 1, 1)
		pat.add_color_stop_rgba (1, 0.9, 0.7, 0.2, 1)

		ctx.new_path()
		ctx.rectangle (0, 0, 1,1)
		ctx.set_source (pat)
		ctx.fill ()

		ctx.restore()
	def DrawGrid(self, ctx):
		ctx.new_path()
		ctx.set_source_rgba (0.3, 0.2, 0.5, 0.1)
		ctx.set_line_width (5)
		ctx.set_line_cap(cairo.LINE_CAP_ROUND)
		for i in range(1, self.__col):
			x = self.__gridwidth * i
			ctx.move_to(x, 5)
			ctx.line_to(x, self.__height-5)
		for j in range(1, self.__row):
			y = self.__gridheight * j
			ctx.move_to(5, y)
			ctx.line_to(self.__width-5, y)
		ctx.stroke()
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

