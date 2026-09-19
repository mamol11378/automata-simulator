import sys, math
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QStackedWidget,
    QFrame, QMessageBox, QComboBox, QCheckBox, QListWidget, QListWidgetItem,
    QHeaderView, QGroupBox, QFormLayout, QInputDialog, QTextEdit
)
from automata import FiniteAutomaton, Transition, EPSILON

AUTHOR = "Mohammadreza Kazemi — ساخته شده توسط محمدرضا کاظمی"

class GraphView(QWidget):
    state_clicked = Signal(str)
    changed = Signal()

    def __init__(self, editable=False):
        super().__init__()
        self.automaton = None
        self.editable = editable
        self.positions = {}
        self.selected = None
        self.dragging = None
        self.edge_mode = False
        self.edge_source = None
        self.flow_edges = []
        self.flow_t = 0.0
        self.setMinimumHeight(430)
        self.setFocusPolicy(Qt.StrongFocus)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_flow)
        self.timer.start(30)

    def set_automaton(self, automaton, active=None, path=None):
        self.automaton = automaton
        self.active = active
        self.path = path or []
        if automaton:
            old = self.positions.copy()
            self.positions = {}
            n = len(automaton.states)
            for i, s in enumerate(automaton.states):
                if s in old:
                    self.positions[s] = old[s]
                else:
                    self.positions[s] = self._default_pos(i, n)
        self.update()

    def _default_pos(self, i, n):
        cx, cy = self.width()/2, self.height()/2
        if n <= 1:
            return QPointF(cx, cy)
        r = min(self.width(), self.height()) * .30
        a = -math.pi/2 + 2*math.pi*i/n
        return QPointF(cx + r*math.cos(a), cy + r*.72*math.sin(a))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.automaton and not self.positions:
            self.set_automaton(self.automaton, getattr(self, "active", None), getattr(self, "path", []))

    def _radius(self):
        return 34

    def _hit_state(self, pt):
        r = self._radius() + 7
        for s, p in self.positions.items():
            if math.hypot(pt.x()-p.x(), pt.y()-p.y()) <= r:
                return s
        return None

    def mouseDoubleClickEvent(self, e):
        if not self.editable or e.button() != Qt.LeftButton:
            return
        if self._hit_state(e.position()) is not None:
            return
        i = 0
        while f"q{i}" in self.automaton.states:
            i += 1
        name = f"q{i}"
        self.automaton.add_state(name)
        self.positions[name] = e.position()
        self.selected = name
        self.changed.emit()
        self.update()

    def mousePressEvent(self, e):
        if not self.editable or e.button() != Qt.LeftButton:
            return
        state = self._hit_state(e.position())
        if self.edge_mode:
            if state:
                if self.edge_source is None:
                    self.edge_source = state
                    self.selected = state
                else:
                    self._create_edge(self.edge_source, state)
                    self.edge_source = None
                self.update()
            return
        if state:
            self.selected = state
            self.dragging = state
            self.state_clicked.emit(state)
        else:
            self.selected = None
        self.update()

    def mouseMoveEvent(self, e):
        if self.editable and self.dragging and not self.edge_mode:
            self.positions[self.dragging] = e.position()
            self.update()

    def mouseReleaseEvent(self, e):
        if self.dragging:
            self.dragging = None
            self.changed.emit()

    def keyPressEvent(self, e):
        if self.editable and e.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.selected:
            self.automaton.remove_state(self.selected)
            self.positions.pop(self.selected, None)
            self.selected = None
            self.changed.emit()
            self.update()
        else:
            super().keyPressEvent(e)

    def _create_edge(self, source, target):
        symbol, ok = QInputDialog.getText(self, self.window().tr("transition"), f"{source} → {target}\n{self.window().tr("symbol_prompt")}")
        if ok and symbol.strip():
            try:
                self.automaton.add_transition(source, symbol.strip(), target)
                self.changed.emit()
            except Exception as ex:
                QMessageBox.warning(self, self.window().tr("transition"), str(ex))

    def _edge_pairs(self):
        pairs = {}
        if not self.automaton:
            return pairs
        for t in self.automaton.transitions:
            pairs.setdefault((t.source, t.target), []).append(t.symbol)
        return pairs

    def _edge_point(self, a, b, t):
        if a == b:
            p = self.positions[a]
            return QPointF(p.x(), p.y()-70)
        p1, p2 = self.positions[a], self.positions[b]
        return QPointF(p1.x()+(p2.x()-p1.x())*t, p1.y()+(p2.y()-p1.y())*t)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#0f131b"))
        if not self.automaton or not self.automaton.states:
            p.setPen(QColor("#64748b"))
            p.setFont(QFont("Segoe UI", 13))
            p.drawText(self.rect(), Qt.AlignCenter, "برای ساخت q0 روی بوم دوبار کلیک کنید" if getattr(self.window(),"lang","en")=="fa" else "Double-click the canvas to create q0")
            return
        pairs = self._edge_pairs()
        active_pairs = set()
        if hasattr(self, "path") and len(self.path) > 1:
            for a, b in zip(self.path, self.path[1:]):
                active_pairs.add((a, b))
        for (a,b), symbols in pairs.items():
            if a not in self.positions or b not in self.positions:
                continue
            active = (a,b) in active_pairs
            self._draw_edge(p, a, b, ", ".join(symbols), active)
        for s, pt in self.positions.items():
            self._draw_state(p, s, pt)

    def _draw_edge(self, p, a, b, label, active):
        p1, p2 = self.positions[a], self.positions[b]
        pen = QPen(QColor("#9b8cff" if active else "#536174"), 3 if active else 2)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        r = self._radius()
        if a == b:
            path = QPainterPath(QPointF(p1.x()-r*.8, p1.y()-r*.45))
            path.cubicTo(p1.x()-80, p1.y()-115, p1.x()+80, p1.y()-115, p1.x()+r*.8, p1.y()-r*.45)
            p.drawPath(path)
            tip = QPointF(p1.x()+r*.8, p1.y()-r*.45)
            back = QPointF(tip.x()-3, tip.y()+14)
            self._arrow(p, tip, back, pen)
            lp = QPointF(p1.x()-12, p1.y()-92)
        else:
            dx,dy=p2.x()-p1.x(),p2.y()-p1.y()
            d=max(math.hypot(dx,dy),1)
            ux,uy=dx/d,dy/d
            x1,y1=p1.x()+ux*r,p1.y()+uy*r
            x2,y2=p2.x()-ux*r,p2.y()-uy*r
            p.drawLine(QPointF(x1,y1),QPointF(x2,y2))
            tip=QPointF(x2,y2)
            back=QPointF(x2-ux*12+uy*7,y2-uy*12-ux*7)
            self._arrow(p,tip,back,pen)
            lp=QPointF((x1+x2)/2-10,(y1+y2)/2-10)
        p.setPen(QColor("#d7dced"))
        p.setFont(QFont("Segoe UI", 10, QFont.Bold))
        p.drawText(lp, label)
        if active:
            t = (self.flow_t % 1.0)
            fp = self._edge_point(a,b,t)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor("#d9d3ff")))
            p.drawEllipse(fp, 5, 5)

    def _arrow(self,p,tip,back,pen):
        dx,dy=tip.x()-back.x(),tip.y()-back.y()
        d=max(math.hypot(dx,dy),1); ux,uy=dx/d,dy/d
        a=QPointF(tip.x()-ux*11+uy*6,tip.y()-uy*11-ux*6)
        b=QPointF(tip.x()-ux*11-uy*6,tip.y()-uy*11+ux*6)
        p.setPen(pen); p.drawLine(tip,a); p.drawLine(tip,b)

    def _draw_state(self,p,s,pt):
        r=self._radius()
        selected=s==self.selected
        active=s==getattr(self,"active",None)
        p.setPen(QPen(QColor("#b5aaff" if selected or active else "#66758a"), 3 if selected or active else 2))
        p.setBrush(QBrush(QColor("#1a202c")))
        p.drawEllipse(pt,r,r)
        if s in self.automaton.finals:
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(pt,r-6,r-6)
        p.setPen(QColor("#f8fafc"))
        p.setFont(QFont("Segoe UI",11,QFont.Bold))
        p.drawText(pt.x()-30,pt.y()-9,60,20,Qt.AlignCenter,s)
        if s==self.automaton.start:
            pen=QPen(QColor("#66758a"),2)
            p.setPen(pen)
            p.drawLine(pt.x()-70,pt.y(),pt.x()-r,pt.y())
            self._arrow(p,QPointF(pt.x()-r,pt.y()),QPointF(pt.x()-r-10,pt.y()-5),pen)

    def _animate_flow(self):
        self.flow_t += .018
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang="en"
        self.machine=self.sample()
        self.current=self.machine.start
        self.path=[self.current]
        self.input_index=0
        self._build()
        self.setLayoutDirection(Qt.LeftToRight)
        self._refresh()

    def sample(self):
        return FiniteAutomaton(
            ["q0","q1","q2"], ["0","1"],
            [Transition("q0","0","q1"),Transition("q0","1","q0"),
             Transition("q1","0","q1"),Transition("q1","1","q2"),
             Transition("q2","0","q2"),Transition("q2","1","q0")],
            "q0", {"q2"})

    def _build(self):
        self.setMinimumSize(1200,780)
        root=QWidget(); self.setCentralWidget(root)
        outer=QHBoxLayout(root); outer.setContentsMargins(0,0,0,0)
        self.sidebar=QFrame(); self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("QFrame{background:#0a0d13;} QPushButton{color:#aeb8c8;background:transparent;border:0;border-radius:8px;padding:13px;text-align:left;font-size:14px;} QPushButton:hover{background:#181d27;color:white;}")
        sl=QVBoxLayout(self.sidebar); sl.setContentsMargins(15,18,15,15)
        self.logo=QLabel("◉  AUTOMATA\n    SIMULATOR")
        self.logo.setStyleSheet("color:#f8fafc;font-size:17px;font-weight:700;padding:10px;")
        sl.addWidget(self.logo)
        self.nav=[]
        for key in ("designer","simulator","table","convert"):
            b=QPushButton(); b.clicked.connect(lambda _,k=key:self.navigate(k)); self.nav.append((key,b)); sl.addWidget(b)
        sl.addStretch()
        self.lang=QPushButton(); self.lang.clicked.connect(self.toggle_lang); sl.addWidget(self.lang)
        self.author=QLabel(AUTHOR); self.author.setWordWrap(True); self.author.setStyleSheet("color:#657185;font-size:10px;padding:10px;"); sl.addWidget(self.author)
        outer.addWidget(self.sidebar)
        self.stack=QStackedWidget(); outer.addWidget(self.stack,1)
        self.stack.addWidget(self._designer())
        self.stack.addWidget(self._simulator())
        self.stack.addWidget(self._table())
        self.stack.addWidget(self._convert())

    def panel(self):
        return "QFrame{background:#151a23;border:1px solid #272f3d;border-radius:12px;} QLabel{color:#aab5c5;} QLineEdit,QComboBox,QListWidget,QTextEdit{background:#0d1118;color:#f4f6fb;border:1px solid #303949;border-radius:7px;padding:8px;} QPushButton{background:#252b39;color:#f7f8fb;border:0;border-radius:7px;padding:9px 13px;} QPushButton:hover{background:#353d50;} QCheckBox{color:#aab5c5;padding:5px;}"

    def _page(self,key):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(28,24,28,22); l.setSpacing(14)
        h=QHBoxLayout(); title=QLabel(); title.setStyleSheet("font-size:25px;font-weight:700;color:#f8fafc;"); h.addWidget(title); h.addStretch()
        badge=QLabel(); badge.setStyleSheet("background:#242039;color:#bdb6ff;padding:7px 14px;border-radius:8px;"); h.addWidget(badge); l.addLayout(h)
        return w,l,title,badge

    def _designer(self):
        w,l,self.dtitle,self.dbadge=self._page("designer")
        top=QFrame(); top.setStyleSheet(self.panel()); tl=QHBoxLayout(top)
        self.add_btn=QPushButton(); self.add_btn.clicked.connect(self.create_state)
        self.edge_btn=QPushButton(); self.edge_btn.setCheckable(True); self.edge_btn.toggled.connect(self.toggle_edge)
        self.start_btn=QPushButton(); self.start_btn.clicked.connect(self.set_start)
        self.final_btn=QPushButton(); self.final_btn.clicked.connect(self.toggle_final)
        self.delete_btn=QPushButton(); self.delete_btn.clicked.connect(self.delete_selected)
        for b in (self.add_btn,self.edge_btn,self.start_btn,self.final_btn,self.delete_btn): tl.addWidget(b)
        tl.addStretch()
        l.addWidget(top)
        self.design_graph=GraphView(editable=True)
        self.design_graph.state_clicked.connect(self.on_graph_state)
        self.design_graph.changed.connect(self._refresh)
        l.addWidget(self.design_graph,1)
        self.design_hint=QLabel(); self.design_hint.setWordWrap(True); self.design_hint.setStyleSheet("color:#738095;padding:4px;"); l.addWidget(self.design_hint)
        return w

    def _simulator(self):
        w,l,self.stitle,self.sbadge=self._page("simulator")
        self.sim_graph=GraphView()
        l.addWidget(self.sim_graph,1)
        bar=QFrame(); bar.setStyleSheet(self.panel()); bl=QHBoxLayout(bar)
        self.input=QLineEdit("0101"); self.input.setMinimumWidth(240)
        self.run=QPushButton(); self.step=QPushButton(); self.reset=QPushButton()
        self.run.clicked.connect(self.run_sim); self.step.clicked.connect(self.step_sim); self.reset.clicked.connect(self.reset_sim)
        self.current_label=QLabel(); self.status=QLabel()
        for x in (self.input,self.run,self.step,self.reset,self.current_label,self.status): bl.addWidget(x)
        l.addWidget(bar)
        self.path_label=QLabel(); self.path_label.setStyleSheet("color:#7e8ca1;padding:3px;"); l.addWidget(self.path_label)
        return w

    def _table(self):
        w,l,self.ttitle,self.tbadge=self._page("table")
        self.tw=QTableWidget(); self.tw.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tw.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l.addWidget(self.tw)
        return w

    def _convert(self):
        w,l,self.ctitle,self.cbadge=self._page("convert")
        bar=QFrame(); bar.setStyleSheet(self.panel()); bl=QHBoxLayout(bar)
        self.convert=QPushButton(); self.convert.clicked.connect(self.convert_nfa); bl.addWidget(self.convert); bl.addStretch(); l.addWidget(bar)
        self.cg=GraphView(); l.addWidget(self.cg,1)
        self.cinfo=QTextEdit(); self.cinfo.setReadOnly(True); self.cinfo.setMaximumHeight(160); l.addWidget(self.cinfo)
        return w

    def create_state(self):
        i=0
        while f"q{i}" in self.machine.states: i+=1
        self.machine.add_state(f"q{i}")
        self._refresh()
        self.design_graph.selected=f"q{i}"
        self.design_graph.update()

    def on_graph_state(self,s):
        self.design_graph.selected=s
        self.design_graph.setFocus()
        self._refresh()

    def toggle_edge(self,on):
        self.design_graph.edge_mode=on
        self.edge_btn.setText(self.tr("edge_mode") if on else self.tr("edge_draw"))

    def set_start(self):
        s=self.design_graph.selected
        if s:
            self.machine.start=s
            self.current=s
            self.path=[s]
            self._refresh()

    def toggle_final(self):
        s=self.design_graph.selected
        if not s:return
        if s in self.machine.finals:self.machine.finals.remove(s)
        else:self.machine.finals.add(s)
        self._refresh()

    def delete_selected(self):
        s=self.design_graph.selected
        if s:
            self.machine.remove_state(s)
            self.design_graph.selected=None
            self._refresh()

    def _refresh(self):
        self._texts()
        self.design_graph.set_automaton(self.machine,self.current,self.path)
        self.sim_graph.set_automaton(self.machine,self.current,self.path)
        self._table_refresh()
        self.current_label.setText(f"{self.tr('current')}: {self.current or '—'}")
        self.status.setText(f"{self.tr('result')}: {self.tr('ready')}")
        self.path_label.setText(f"{self.tr('path')}: " + " → ".join(self.path))
        if self.design_graph.selected in self.machine.states:
            self.design_graph.selected=self.design_graph.selected

    def _table_refresh(self):
        self.tw.setColumnCount(len(self.machine.alphabet)+1)
        self.tw.setHorizontalHeaderLabels([self.tr("state")]+self.machine.alphabet)
        self.tw.setRowCount(len(self.machine.states))
        for r,s in enumerate(self.machine.states):
            self.tw.setItem(r,0,QTableWidgetItem(("→ " if s==self.machine.start else "")+("* " if s in self.machine.finals else "")+s))
            for c,sym in enumerate(self.machine.alphabet,1):
                ds=sorted(self.machine.destinations(s,sym))
                self.tw.setItem(r,c,QTableWidgetItem(", ".join(ds) if ds else "—"))

    def tr(self,k):
        fa={
        "designer":"طراحی ماشین","simulator":"شبیه‌ساز","table":"جدول انتقال","convert":"NFA → DFA",
        "current":"حالت فعلی","result":"نتیجه","ready":"آماده","run":"اجرا","step":"مرحله بعد","reset":"بازنشانی",
        "draw":"رسم انتقال","start":"شروع","final":"نهایی","delete":"حذف حالت","state":"حالت","path":"مسیر",
        "convert_now":"تبدیل NFA فعلی به DFA","accepted":"پذیرفته شد ✓","rejected":"رد شد ✕","add_state":"+ حالت","edge_mode":"✓ حالت رسم","edge_draw":"رسم انتقال","hint":"دوبارکلیک = حالت جدید  •  کشیدن = جابه‌جایی  •  رسم انتقال = اتصال دو حالت  •  Delete = حذف حالت","error":"خطا","conversion":"تبدیل","set_start_first":"ابتدا یک حالت شروع تعیین کنید.","already_dfa":"ماشین فعلی از قبل DFA است.","dfa_created":"DFA با روش ساخت زیرمجموعه‌ای ساخته شد","states":"حالت‌ها","start_state":"شروع","final_states":"نهایی","transitions":"انتقال‌ها","no_final":"—","transition":"انتقال","symbol_prompt":"نماد (0، 1، ε):"
        }
        en={
        "designer":"Designer","simulator":"Simulator","table":"Transition Table","convert":"NFA → DFA",
        "current":"Current State","result":"Result","ready":"Ready","run":"Run","step":"Step","reset":"Reset",
        "draw":"Draw Transition","start":"Set Start","final":"Toggle Final","delete":"Delete State","state":"State","path":"Path",
        "convert_now":"Convert current NFA to DFA","accepted":"Accepted ✓","rejected":"Rejected ✕","add_state":"+ State","edge_mode":"✓ Edge mode","edge_draw":"Draw Transition","hint":"Double-click = new state  •  Drag = move  •  Draw Transition = connect two states  •  Delete = remove selected state","error":"Error","conversion":"Conversion","set_start_first":"Set a start state first.","already_dfa":"The current machine is already a DFA.","dfa_created":"DFA created by subset construction","states":"States","start_state":"Start","final_states":"Final","transitions":"Transitions","no_final":"—","transition":"Transition","symbol_prompt":"Symbol (0, 1, ε):"
        }
        return (fa if self.lang=="fa" else en).get(k,k)

    def _texts(self):
        for k,b in self.nav:b.setText(self.tr(k))
        self.lang.setText("فارسی / English")
        self.dtitle.setText(self.tr("designer")); self.stitle.setText(self.tr("simulator"))
        self.ttitle.setText(self.tr("table")); self.ctitle.setText(self.tr("convert"))
        typ="DFA" if self.machine.is_deterministic() else "NFA"
        for b in (self.dbadge,self.sbadge,self.tbadge,self.cbadge):b.setText(typ)
        self.add_btn.setText(self.tr("add_state"))
        self.start_btn.setText(self.tr("start")); self.final_btn.setText(self.tr("final")); self.delete_btn.setText(self.tr("delete"))
        self.edge_btn.setText(self.tr("edge_mode") if self.edge_btn.isChecked() else self.tr("edge_draw"))
        self.run.setText(self.tr("run")); self.step.setText(self.tr("step")); self.reset.setText(self.tr("reset"))
        self.convert.setText(self.tr("convert_now"))
        self.design_hint.setText(self.tr("hint"))

    def navigate(self,k):
        self.stack.setCurrentIndex({"designer":0,"simulator":1,"table":2,"convert":3}[k])

    def reset_sim(self):
        self.current=self.machine.start
        self.input_index=0
        self.path=[self.current] if self.current else []
        self._refresh()

    def run_sim(self):
        text=self.input.text().strip()
        try:
            if not self.machine.start: raise ValueError(self.tr("set_start_first"))
            if self.machine.is_deterministic():
                ok,path=self.machine.simulate_dfa(text)
                self.current=path[-1]; self.path=path
            else:
                ok,paths=self.machine.simulate_nfa(text)
                self.path=["{" + ",".join(sorted(x)) + "}" for x in paths]
                self.current=self.path[-1]
            self.sim_graph.set_automaton(self.machine,self.current,self.path)
            self.current_label.setText(f"{self.tr('current')}: {self.current}")
            self.status.setText(f"{self.tr('result')}: {self.tr('accepted') if ok else self.tr('rejected')}")
            self.path_label.setText(f"{self.tr('path')}: " + " → ".join(self.path))
        except Exception as ex: QMessageBox.warning(self,self.tr("error"),str(ex))

    def step_sim(self):
        text=self.input.text().strip()
        try:
            if not self.machine.start: raise ValueError("Set a start state first.")
            if self.input_index==0:
                self.current=self.machine.start; self.path=[self.current]
            if self.input_index>=len(text):
                ok=self.current in self.machine.finals
                self.status.setText(f"{self.tr('result')}: {self.tr('accepted') if ok else self.tr('rejected')}")
                return
            ch=text[self.input_index]
            if not self.machine.is_deterministic():
                _,paths=self.machine.simulate_nfa(text[:self.input_index+1])
                states=paths[-1]; self.current="{" + ",".join(sorted(states)) + "}"
            else:
                self.current=self.machine.step_dfa(self.current,ch)
            self.path.append(self.current); self.input_index+=1
            self.sim_graph.set_automaton(self.machine,self.current,self.path)
            self.current_label.setText(f"{self.tr('current')}: {self.current}")
            self.path_label.setText(f"{self.tr('path')}: " + " → ".join(self.path))
        except Exception as ex: QMessageBox.warning(self,"Error",str(ex))

    def convert_nfa(self):
        try:
            if self.machine.is_deterministic(): raise ValueError(self.tr("already_dfa"))
            dfa=self.machine.to_dfa()
            self.cg.set_automaton(dfa,dfa.start)
            lines=[self.tr("dfa_created"),"",f"{self.tr("states")}: {', '.join(dfa.states)}",f"{self.tr("start_state")}: {dfa.start}",f"{self.tr("final_states")}: {', '.join(sorted(dfa.finals)) or self.tr("no_final")}","",f"{self.tr("transitions")}:"]
            lines += [f"{t.source} --{t.symbol}--> {t.target}" for t in dfa.transitions]
            self.cinfo.setPlainText("\n".join(lines))
        except Exception as ex: QMessageBox.warning(self,self.tr("conversion"),str(ex))

    def toggle_lang(self):
        self.lang="fa" if self.lang=="en" else "en"
        self.setLayoutDirection(Qt.RightToLeft if self.lang=="fa" else Qt.LeftToRight)
        self._refresh()

if __name__=="__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion")
    app.setStyleSheet("QMainWindow,QWidget{background:#10141c;color:#e5e7eb;font-family:'Segoe UI';} QHeaderView::section{background:#1b212c;color:#cbd5e1;padding:8px;border:0;} QTableWidget{background:#121720;color:#e5e7eb;gridline-color:#303746;border:1px solid #272f3d;}")
    win=MainWindow(); win.show(); sys.exit(app.exec())
