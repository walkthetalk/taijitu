#!/usr/bin/env python2
# coding=utf-8
import os
import sys

import re
import fileinput
import time

import wx

self_dir = os.path.realpath(sys.path[0])
sys.path.append(self_dir + '/lib')

import buildRepresent
import TaiJiTu as taijitu

class cmmstate:
	def __init__(self, nodedict):
		self.__state = dict()
		for item in nodedict:
			self.__state[item] = False
	def isXXed(self, item):
		return self.__state[item]
	def setXXed(self, item):
		self.__state[item] = True

class cmmnode:
	__build_scipt = self_dir + "/optimus-build"
	def __init__(self, description):
		desc = re.split("\t*", description)
		print(desc)
		self.key = desc[0]
		self.__label = desc[1]
		coorstr = re.split(",", desc[2])
		self.__pos = (float(coorstr[0]), float(coorstr[1]))
		self.depKeys = []
		if (len(desc) > 3):
			self.depKeys = re.split(",", desc[3])
		self.__depRelation = []
		self.__rdepRelation = []
		self.__depth = -1
	def build_depends(self, nodedict, relationdict):
		for onedep in self.depKeys:
			depnode = nodedict[onedep]
			relation = cmmRelation(depnode, self)
			relationdict[relation.get_key()] = relation
			self.__depRelation.append(relation)
			depnode.__add_rdepRelation(relation)
	def __add_rdepRelation(self, relation):
		self.__rdepRelation.append(relation)
	def get_rdep_relation(self):
		return self.__rdepRelation
	def get_key(self):
		return self.key
	def get_label(self):
		return self.__label
	def get_pos(self):
		return self.__pos
	def get_depth(self):
		return self.__depth
	def is_leaf(self):
		return (len(self.__rdepRelation) == 0)
	def generate_depth(self):
		if self.__depth == -1:
			newdepth = 0
			for item in self.__depRelation:
				depnode = item.getStart()
				depnode.generate_depth()
				tmpdepth = depnode.get_depth() + 1
				if newdepth < tmpdepth:
					newdepth = tmpdepth
			self.__depth = newdepth
	def set_drawinfo(self, drawinfo):
		self.__drawinfo = drawinfo
	def get_drawinfo(self):
		return self.__drawinfo

	def prepare4exe(self, dep, state, workq):
		if state.isXXed(self.get_key()):
			return
		if dep:
			for item in self.__depRelation:
				item.getStart().prepare4exe(dep, state, workq)
		# execute
		workq.put(self)
		state.setXXed(self.get_key())
	def exe(self):
		di = self.__drawinfo
		di.StartBuild()

		build_cmd = self.__build_scipt + " " + self.get_key()
		os.system(build_cmd + " -f -c cleanall")
		time.sleep(1)

		build_cmd_postfix = ""
		if re.match('.+-image-.+', self.get_key()) != None:
			build_cmd_postfix = " and extract"
		os.system(build_cmd + build_cmd_postfix)

		di.EndBuild()

class cmmRelation():
	def __init__(self, depnode, rdepnode):
		self.__start = depnode
		self.__end = rdepnode
	def get_key(self):
		return self.__start.get_key() + self.__end.get_key()
	def getStart(self):
		return self.__start
	def getEnd(self):
		return self.__end
	def set_drawinfo(self, drawinfo):
		self.__drawinfo = drawinfo
	def get_drawinfo(self):
		return self.__drawinfo

class MainFrame(wx.Frame):
	def __init__(self,parent,title,nodedict,relationdict):
		wx.Frame.__init__(self,parent,title=title,pos=(200,200),
			size=(500,500))

		self.__nodedict = nodedict
		self.__relationdict = relationdict
		self.__dep = False

		# UI
		## menubar
		menubar = wx.MenuBar()

		fileMenu = wx.Menu()
		fitem = fileMenu.Append(wx.ID_EXIT, "&Quit", "退出程序")
		self.Bind(wx.EVT_MENU, self.OnQuit, fitem)

		prefMenu = wx.Menu()
		pdep = prefMenu.Append(wx.ID_ANY, "&Consider Dependency",
			"编译时考虑依赖关系", kind = wx.ITEM_CHECK)
		self.Bind(wx.EVT_MENU, self.OnDep, pdep)

		helpMenu = wx.Menu()
		habout = helpMenu.Append(wx.ID_ANY, "&About",
			"关于")
		self.Bind(wx.EVT_MENU, self.OnAbout, habout)

		menubar.Append(fileMenu, "&File")
		menubar.Append(prefMenu, "&Preference")
		menubar.Append(helpMenu, "&Help")
		self.SetMenuBar(menubar)

		tjt = taijitu.TaiJiTu(self, 200,200)
		icon = wx.EmptyIcon()
		icon.CopyFromBitmap(tjt.ToWxBitmap())
		self.SetIcon(icon)

		## toolbar
		#toolbar = self.CreateToolBar()
		#toolbar.AddCheckTool(wx.ID_ANY, wx.Bitmap("a.bmp"))
		#toolbar.Realize()

		# EVENT
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_MOTION, self.OnMotion)
		self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
		self.Bind(wx.EVT_SIZE, self.OnSize)

		#---------add quit button-----------------------------
		#self.testbuttion = wx.Button(self,label="test",
		#	pos=(300,200),size=(50,50))
		#self.testbuttion = wx.Button(self,label="test",
		#	pos=(0,0),size=(50,50))
		#self.testsbutton = polybutton.SButton(self,label="sbutton",
		#	pos=(10,10), size=(200,200))

		self.__sidewidth = 5
		(width, height) = self.GetClientSizeTuple()
		self.__st = buildRepresent.StepTree(self,
			width=width-self.__sidewidth*2,
			height=height - self.__sidewidth*2,
			nodedict=self.__nodedict,
			relationdict = self.__relationdict)

		self.__timerBR = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.OnTimerBR,
			self.__timerBR)
		self.__timerBR_DI = None

	def OnPaint(self, event):

		dc = wx.GCDC(self)
		dc.SetBackgroundMode(wx.SOLID)
		dc.Clear()
		bmp = self.__st.ToWxBitmap()
		dc.DrawBitmap(bmp,self.__sidewidth,self.__sidewidth)
	def OnMotion(self, event):
		if not self.IsEnabled():
			return

		#if event.LeftIsDown() and self.HasCapture():
		(new, old) = self.__st.OnMotion(
				event.GetX() - self.__sidewidth,
				event.GetY() - self.__sidewidth)

		if new != old:
			self.Refresh()

		if new == None:
			event.Skip()
	def OnLeftDown(self, event):
		if not self.IsEnabled():
			return

		(new, old) = self.__st.OnMotion(
				event.GetX() - self.__sidewidth,
				event.GetY() - self.__sidewidth)
		if new == None:
			event.Skip()
			return

		self.__st.SetLeftDown(True)

		if not self.HasCapture():
			self.CaptureMouse()

		self.SetFocus()

		self.Refresh()
	def OnLeftUp(self, event):
		if not self.IsEnabled() or not self.HasCapture():
			return

		if self.HasCapture():
			self.ReleaseMouse()

		(new, old) = self.__st.OnMotion(
				event.GetX() - self.__sidewidth,
				event.GetY() - self.__sidewidth)

		self.__st.SetLeftDown(False)

		self.Refresh()

		if new == None:
			event.Skip()
		else:
			new.prepare4exe(self.__dep,
				cmmstate(self.__nodedict))
	def OnQuit(self, e):
		self.Close()

	def OnDep(self, evt):
		self.__dep = evt.Checked()
	def OnAbout(self, evt):
		aboutDlg = wx.MessageDialog(self, "^_^", "关于", wx.OK)
		aboutDlg.ShowModal()
	def OnSize(self, evt):
		(w, h) = self.GetClientSizeTuple()
		self.__st.OnSize(w-self.__sidewidth*2, h-self.__sidewidth*2)

	def OnTimerBR(self, evt):
		self.__timerBR_DI.IncBuildProgress()
		self.Refresh()
	def StartBuildTimer(self, nDI):
		self.__timerBR_DI = nDI
		self.__timerBR.Start(100)
	def EndBuildTimer(self):
		self.__timerBR.Stop()
		self.__timerBR_DI = None
		self.Refresh()

def main():
	# read configuration file
	nodedict = dict()
	for line in fileinput.input(self_dir + "conf/steps.conf"):
		line_tmp = re.sub("\n$","",line)
		if (line_tmp == ""):
			continue
		node = cmmnode(line_tmp)
		nodedict[node.get_key()] = node
	# 构造无环图
	relationdict = dict()
	for item in nodedict:
		nodedict[item].build_depends(nodedict, relationdict)
	# 计算深度，起始值为0
	for item in nodedict:
		if nodedict[item].is_leaf():
			nodedict[item].generate_depth()

	# print
	for item in nodedict:
		print (nodedict[item].get_key())
		print (nodedict[item].get_depth())
		
	# start window
	app = wx.App(False)
	frame = MainFrame(None,title="太极图",
			nodedict = nodedict,
			relationdict = relationdict)
	frame.SetTransparent(200) 
	frame.Show()
	app.MainLoop()
if __name__ =="__main__":
	main()

