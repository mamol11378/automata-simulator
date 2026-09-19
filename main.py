import sys, math
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QStackedWidget,
    QFrame, QMessageBox, QComboBox, QCheckBox, QListWidget, QListWidgetItem,
    QHeaderView, QGroupBox, QFormLayout, QSplitter, QTextEdit
)
from automata import FiniteAutomaton, Transition, EPSILON

AUTHOR = "Mohammadreza Kazemi — ساخته شده توسط محمدرضا کاظمی"

S = {
"en": {
"title":"Automata Simulator","designer":"Designer","simulator":"Simulator",
"table":"Transition Table","convert":"NFA → DFA","input":"Input String",
"run":"Run","step":"Step","reset":"Reset","add":"Add","remove":"Remove",
"state":"State","states":"States","transitions":"Transitions","start":"Start",
"final":"Final","source":"From","target":"To","symbol":"Symbol","set_start":"Set Start",
"add_transition":"Add Transition","clear":"Clear","automaton":"Automaton",
"ready":"Ready","accepted":"Accepted ✓","rejected":"Rejected ✕","invalid":"Invalid",
"language":"فارسی / English","created":"Created by Mohammadreza Kazemi",
"dfa":"DFA","nfa":"NFA","convert_now":"Convert current NFA to DFA",
"conversion_result":"Conversion Result","select_state":"Select state",
"delete_state":"Delete selected state","add_state":"Add state","alphabet":"Alphabet",
"step_info":"Step","current":"Current","path":"Path","error":"Error",
"converted":"NFA converted to DFA successfully.","empty":"No states yet.",
"about":"A visual learning tool for Formal Languages and Automata Theory.",
"state_name":"State name","final_hint":"Accepting state","start_hint":"Initial state",
"sample":"Sample","apply":"Apply","result":"Result","export":"Export"
},
"fa": {
"title":"شبیه‌ساز ماشین متناهی","designer":"طراحی ماشین","simulator":"شبیه‌ساز",
"table":"جدول انتقال","convert":"NFA → DFA","input":"رشته ورودی",
"run":"اجرا","step":"مرحله بعد","reset":"بازنشانی","add":"افزودن","remove":"حذف",
"state":"حالت","states":"حالت‌ها","transitions":"انتقال‌ها","start":"شروع",
"final":"نهایی","source":"مبدأ","target":"مقصد","symbol":"نماد","set_start":"تعیین شروع",
"add_transition":"افزودن انتقال","clear":"پاک کردن","automaton":"ماشین",
"ready":"آماده","accepted":"پذیرفته شد ✓","rejected":"رد شد ✕","invalid":"نامعتبر",
"language":"فارسی / English","created":"ساخته شده توسط محمدرضا کاظمی",
"dfa":"DFA","nfa":"NFA","convert_now":"تبدیل NFA فعلی به DFA",
"conversion_result":"نتیجه تبدیل","select_state":"انتخاب حالت",
"delete_state":"حذف حالت انتخاب‌شده","add_state":"افزودن حالت","alphabet":"الفبا",
"step_info":"مرحله","current":"فعلی","path":"مسیر","error":"خطا",
"converted":"NFA با موفقیت به DFA تبدیل شد.","empty":"هنوز حالتی وجود ندارد.",
"about":"ابزار آموزشی تصویری برای درس نظریه زبان‌ها و ماشین‌ها.",
"state_name":"نام حالت","final_hint":"حالت پذیرش","start_hint":"حالت شروع",
"sample":"نمونه","apply":"اعمال","result":"نتیجه","export":"خروجی"
}
}

def color(hexv): return QColor(hexv)

class GraphView(QWidget):
    clicked_state = Signal(str)
    def __init__(self):
        super().__init__()
        self.automaton = None
        self.active = None
        self.path = []
        self.setMinimumHeight(390)
        self.setStyleSheet("background:#10131a;border:1px solid #252b38;border-radius:12px;")
    
    def set_automaton(self, automaton, active=None, path=None):
        self.automaton = automaton
        self.active = active
        self.path = path or []
        self.update()
    
    def _positions(self):
        states = self.automaton.states if self.automaton else []
        n = len(states)
        if not n: return {}
        cx, cy = self.width()/2, self.height()/2 + 5
        rx, ry = max(150, self.width()/2-90), max(95, self.height()/2-85)
        if n == 1: return {states[0]: QPointF(cx,cy)}
        return {s: QPointF(cx+rx*math.cos(-math.pi/2+2*math.pi*i/n),
                           cy+ry*math.sin(-math.pi/2+2*math.pi*i/n)) for i,s in enumerate(states)}
    
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), color("#10131a"))
        if not self.automaton or not self.automaton.states:
            p.setPen(color("#64748b")); p.setFont(QFont("Segoe UI",12))
            p.drawText(self.rect(), Qt.AlignCenter, "Add states in Designer")
            return
        pos=self._positions()
        radius=34
        grouped={}
        for t in self.automaton.transitions:
            grouped.setdefault((t.source,t.target),[]).append(t.symbol)
        for (a,b), symbols in grouped.items():
            if a not in pos or b not in pos: continue
            src,dst=pos[a],pos[b]
            active_edge=(a==self.active and b==self.active) or (len(self.path)>1 and
                any(self.path[i]==a and self.path[i+1]==b for i in range(len(self.path)-1)))
            pen=QPen(color("#8b7cff" if active_edge else "#596579"),3 if active_edge else 2)
            label=", ".join(symbols)
            if a==b:
                path=QPainterPath(QPointF(src.x()-radius,src.y()-radius/2))
                path.cubicTo(src.x()-95,src.y()-115,src.x()+95,src.y()-115,src.x()+radius,src.y()-radius/2)
                p.setPen(pen); p.setBrush(Qt.NoBrush); p.drawPath(path)
                p.drawText(QPointF(src.x()-18,src.y()-92),label)
                self._arrow(p,QPointF(src.x()+radius,src.y()-radius/2),
                            QPointF(src.x()+radius-3,src.y()-radius/2+12),pen)
            else:
                dx,dy=dst.x()-src.x(),dst.y()-src.y(); d=max(math.hypot(dx,dy),1)
                ux,uy=dx/d,dy/d
                x1,y1=src.x()+ux*radius,src.y()+uy*radius
                x2,y2=dst.x()-ux*radius,dst.y()-uy*radius
                p.setPen(pen); p.drawLine(QPointF(x1,y1),QPointF(x2,y2))
                self._arrow(p,QPointF(x2,y2),QPointF(x2-ux*12+uy*7,y2-uy*12-ux*7),pen)
                p.setPen(color("#cbd5e1")); p.drawText(QPointF((x1+x2)/2-8,(y1+y2)/2-10),label)
        for name,pt in pos.items():
            active=name==self.active
            p.setPen(QPen(color("#a394ff" if active else "#64748b"),3))
            p.setBrush(QBrush(color("#1a1e2a")))
            p.drawEllipse(pt,radius,radius)
            if name in self.automaton.finals:
                p.setBrush(Qt.NoBrush); p.drawEllipse(pt,radius-6,radius-6)
            p.setPen(color("#f8fafc")); p.setFont(QFont("Segoe UI",11,QFont.Bold))
            p.drawText(pt.x()-30,pt.y()-8,60,20,Qt.AlignCenter,name)
            if name==self.automaton.start:
                pen=QPen(color("#64748b"),2)
                p.setPen(pen); p.drawLine(pt.x()-72,pt.y(),pt.x()-radius,pt.y())
                self._arrow(p,QPointF(pt.x()-radius,pt.y()),QPointF(pt.x()-radius-10,pt.y()-6),pen)
    
    def _arrow(self,p,tip,back,pen):
        dx,dy=tip.x()-back.x(),tip.y()-back.y(); d=max(math.hypot(dx,dy),1)
        ux,uy=dx/d,dy/d
        a=QPointF(tip.x()-ux*11+uy*6,tip.y()-uy*11-ux*6)
        b=QPointF(tip.x()-ux*11-uy*6,tip.y()-uy*11+ux*6)
        p.setPen(pen); p.drawLine(tip,a); p.drawLine(tip,b)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang="en"; self.page=0
        self.machine=self.sample_machine()
        self.current=self.machine.start
        self.input_text=""; self.input_index=0; self.path=[self.current]
        self.setMinimumSize(1180,760)
        self._build()
        self._refresh_all()
    
    def sample_machine(self):
        return FiniteAutomaton(
            ["q0","q1","q2"],["0","1"],
            [Transition("q0","0","q1"),Transition("q0","1","q0"),
             Transition("q1","0","q1"),Transition("q1","1","q2"),
             Transition("q2","0","q2"),Transition("q2","1","q0")],
            "q0",{"q2"})
    
    def tr(self,k): return S[self.lang][k]
    
    def _build(self):
        self.setWindowTitle(self.tr("title"))
        root=QWidget(); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        self.sidebar=QFrame(); self.sidebar.setFixedWidth(215)
        self.sidebar.setStyleSheet("""QFrame{background:#0b0e14;} QPushButton{color:#aab4c3;background:transparent;border:0;border-radius:7px;padding:12px;text-align:left;font-size:14px;} QPushButton:hover{background:#171b25;color:white;}""")
        sl=QVBoxLayout(self.sidebar); sl.setContentsMargins(15,18,15,15)
        self.logo=QLabel("◉  AUTOMATA\n    SIMULATOR"); self.logo.setStyleSheet("color:#f8fafc;font-size:17px;font-weight:700;padding:10px;"); sl.addWidget(self.logo)
        self.nav=[]
        for key in ("designer","simulator","table","convert"):
            b=QPushButton(); b.clicked.connect(lambda _,k=key:self.navigate(k)); self.nav.append((key,b)); sl.addWidget(b)
        sl.addStretch(); self.lang_btn=QPushButton(); self.lang_btn.clicked.connect(self.toggle_lang); sl.addWidget(self.lang_btn)
        self.author=QLabel(); self.author.setWordWrap(True); self.author.setStyleSheet("color:#64748b;font-size:11px;padding:10px;"); sl.addWidget(self.author)
        outer.addWidget(self.sidebar)
        self.stack=QStackedWidget(); outer.addWidget(self.stack,1)
        self.designer=self._designer_page(); self.simulator=self._simulator_page(); self.table=self._table_page(); self.converter=self._converter_page()
        for w in (self.designer,self.simulator,self.table,self.converter): self.stack.addWidget(w)
    
    def _base(self,key):
        w=QWidget(); lay=QVBoxLayout(w); lay.setContentsMargins(28,24,28,22); lay.setSpacing(15)
        head=QHBoxLayout(); title=QLabel(); title.setObjectName("pageTitle"); title.setProperty("key",key); title.setStyleSheet("font-size:25px;font-weight:700;color:#f8fafc;")
        head.addWidget(title); head.addStretch(); badge=QLabel(); badge.setStyleSheet("background:#242039;color:#b9b1ff;padding:7px 14px;border-radius:8px;"); badge.setProperty("badge",True); head.addWidget(badge); lay.addLayout(head)
        return w,lay,title,badge
    
    def _designer_page(self):
        w,lay,title,badge=self._base("designer"); self.d_title=title; self.d_badge=badge
        splitter=QSplitter(Qt.Horizontal); splitter.setChildrenCollapsible(False)
        left=QFrame(); left.setStyleSheet(self.panel_style()); ll=QVBoxLayout(left)
        self.state_name=QLineEdit(); self.state_name.setPlaceholderText("q3")
        add_state=QPushButton(); add_state.clicked.connect(self.add_state)
        self.state_list=QListWidget(); self.state_list.currentItemChanged.connect(self.select_state)
        del_state=QPushButton(); del_state.clicked.connect(self.delete_state)
        self.start_check=QCheckBox(); self.final_check=QCheckBox()\n        self.start_check.stateChanged.connect(self.set_state_flags); self.final_check.stateChanged.connect(self.set_state_flags)
        ll.addWidget(QLabel("State name")); ll.addWidget(self.state_name); ll.addWidget(add_state); ll.addWidget(self.state_list,1)
        ll.addWidget(del_state); ll.addWidget(self.start_check); ll.addWidget(self.final_check)
        form=QGroupBox(); fl=QFormLayout(form)
        self.from_box=QComboBox(); self.to_box=QComboBox(); self.symbol_box=QLineEdit(); self.symbol_box.setPlaceholderText("0 or ε")
        self.add_trans=QPushButton(); self.add_trans.clicked.connect(self.add_transition)
        fl.addRow(QLabel("From"),self.from_box); fl.addRow(QLabel("To"),self.to_box); fl.addRow(QLabel("Symbol"),self.symbol_box); fl.addRow(self.add_trans)
        ll.addWidget(form)
        self.trans_list=QListWidget(); remove_t=QPushButton(); remove_t.clicked.connect(self.remove_transition)
        ll.addWidget(self.trans_list,1); ll.addWidget(remove_t)
        right=QFrame(); rl=QVBoxLayout(right); self.design_graph=GraphView(); rl.addWidget(self.design_graph,1)
        hint=QLabel(); hint.setWordWrap(True); hint.setStyleSheet("color:#64748b;padding:5px;"); self.design_hint=hint; rl.addWidget(hint)
        splitter.addWidget(left); splitter.addWidget(right); splitter.setSizes([360,700]); lay.addWidget(splitter,1)
        return w
    
    def _simulator_page(self):
        w,lay,title,badge=self._base("simulator"); self.s_title=title; self.s_badge=badge
        self.sim_graph=GraphView(); lay.addWidget(self.sim_graph,1)
        panel=QFrame(); panel.setStyleSheet(self.panel_style()); pl=QHBoxLayout(panel)
        self.input_edit=QLineEdit("0101"); self.input_edit.setMinimumWidth(220)
        self.run_btn=QPushButton(); self.step_btn=QPushButton(); self.reset_btn=QPushButton()
        self.run_btn.clicked.connect(self.run_sim); self.step_btn.clicked.connect(self.step_sim); self.reset_btn.clicked.connect(self.reset_sim)
        self.current_label=QLabel(); self.status_label=QLabel()
        for x in (self.input_edit,self.run_btn,self.step_btn,self.reset_btn,self.current_label,self.status_label): pl.addWidget(x)
        lay.addWidget(panel)
        self.path_label=QLabel(); self.path_label.setStyleSheet("color:#94a3b8;padding:4px;"); lay.addWidget(self.path_label)
        return w
    
    def _table_page(self):
        w,lay,title,badge=self._base("table"); self.t_title=title; self.t_badge=badge
        self.table_widget=QTableWidget(); self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.table_widget); return w
    
    def _converter_page(self):
        w,lay,title,badge=self._base("convert"); self.c_title=title; self.c_badge=badge
        top=QFrame(); top.setStyleSheet(self.panel_style()); tl=QHBoxLayout(top)
        self.convert_btn=QPushButton(); self.convert_btn.clicked.connect(self.convert_nfa); tl.addWidget(self.convert_btn); tl.addStretch()
        lay.addWidget(top)
        self.convert_graph=GraphView(); lay.addWidget(self.convert_graph,1)
        self.convert_info=QTextEdit(); self.convert_info.setReadOnly(True); self.convert_info.setMaximumHeight(145); lay.addWidget(self.convert_info)
        return w
    
    def panel_style(self):
        return """QFrame{background:#151923;border:1px solid #262c38;border-radius:10px;} QLabel{color:#aab4c3;} QLineEdit,QComboBox,QListWidget,QTextEdit{background:#0f1218;color:#f8fafc;border:1px solid #303746;border-radius:7px;padding:7px;} QPushButton{background:#25283a;color:#f8fafc;border:0;border-radius:7px;padding:8px 13px;} QPushButton:hover{background:#353956;} QCheckBox{color:#aab4c3;padding:5px;} QGroupBox{border:1px solid #303746;border-radius:8px;color:#94a3b8;margin-top:8px;padding-top:8px;}"""
    
    def add_state(self):
        try:
            name=self.state_name.text().strip()
            self.machine.add_state(name)
            self.state_name.clear()
            self._refresh_all()
            self._select_name(name)
        except Exception as e: self.show_error(str(e))
    
    def delete_state(self):
        item=self.state_list.currentItem()
        if not item: return
        self.machine.remove_state(item.data(Qt.UserRole))
        self._refresh_all()
    
    def select_state(self,current,previous=None):
        if not current: return
        name=current.data(Qt.UserRole); self.start_check.setChecked(self.machine.start==name); self.final_check.setChecked(name in self.machine.finals)
    
    def set_state_flags(self):
        item=self.state_list.currentItem()
        if not item: return
        name=item.data(Qt.UserRole)
        if self.start_check.isChecked(): self.machine.start=name
        elif self.machine.start==name: self.machine.start=None
        if self.final_check.isChecked(): self.machine.finals.add(name)
        else: self.machine.finals.discard(name)
        self._refresh_all()
    
    def add_transition(self):
        try:
            self.machine.add_transition(self.from_box.currentText(),self.symbol_box.text().strip(),self.to_box.currentText())
            self.symbol_box.clear(); self._refresh_all()
        except Exception as e: self.show_error(str(e))
    
    def remove_transition(self):
        item=self.trans_list.currentItem()
        if not item: return
        idx=item.data(Qt.UserRole)
        if 0 <= idx < len(self.machine.transitions): self.machine.transitions.pop(idx)
        self._refresh_all()
    
    def _select_name(self,name):
        for i in range(self.state_list.count()):
            if self.state_list.item(i).data(Qt.UserRole)==name:
                self.state_list.setCurrentRow(i); break
    
    def _refresh_all(self):
        self._refresh_text()
        self._refresh_designer()
        self._refresh_table()
        self.sim_graph.set_automaton(self.machine,self.current,self.path)
        self.design_graph.set_automaton(self.machine,self.current,self.path)
        self.current_label.setText(f"{self.tr('current')}: {self.current or '—'}")
        self.status_label.setText(f"{self.tr('result')}: {self.tr('ready')}")
        self.path_label.setText(f"{self.tr('path')}: " + " → ".join(self.path))
    
    def _refresh_designer(self):
        self.state_list.blockSignals(True); self.state_list.clear()
        for s in self.machine.states:
            item=QListWidgetItem(("★ " if s==self.machine.start else "")+("* " if s in self.machine.finals else "")+s)
            item.setData(Qt.UserRole,s); self.state_list.addItem(item)
        self.state_list.blockSignals(False)
        if self.machine.start: self._select_name(self.machine.start)
        self.from_box.clear(); self.to_box.clear()
        self.from_box.addItems(self.machine.states); self.to_box.addItems(self.machine.states)
        self.trans_list.clear()
        for i,t in enumerate(self.machine.transitions):
            item=QListWidgetItem(f"{t.source}  —[{t.symbol}]→  {t.target}"); item.setData(Qt.UserRole,i); self.trans_list.addItem(item)
    
    def _refresh_table(self):
        cols=["State"]+self.machine.alphabet
        self.table_widget.setColumnCount(len(cols)); self.table_widget.setHorizontalHeaderLabels(cols)
        self.table_widget.setRowCount(len(self.machine.states))
        for r,s in enumerate(self.machine.states):
            self.table_widget.setItem(r,0,QTableWidgetItem(("→ " if s==self.machine.start else "")+("* " if s in self.machine.finals else "")+s))
            for c,sym in enumerate(self.machine.alphabet,1):
                dest=sorted(self.machine.destinations(s,sym))
                self.table_widget.setItem(r,c,QTableWidgetItem(", ".join(dest) if dest else "—"))
    
    def _refresh_text(self):
        self.setWindowTitle(self.tr("title"))
        for key,b in self.nav: b.setText(self.tr(key))
        self.lang_btn.setText(self.tr("language")); self.author.setText(self.tr("created"))
        for obj,key in ((self.d_title,"designer"),(self.s_title,"simulator"),(self.t_title,"table"),(self.c_title,"convert")): obj.setText(self.tr(key))
        for b in (self.d_badge,self.s_badge,self.t_badge,self.c_badge): b.setText(self.tr("dfa") if self.machine.is_deterministic() else self.tr("nfa"))
        self.run_btn.setText(self.tr("run")); self.step_btn.setText(self.tr("step")); self.reset_btn.setText(self.tr("reset"))
        self.input_edit.setPlaceholderText(self.tr("input"))
        self.convert_btn.setText(self.tr("convert_now"))
        self.add_trans.setText(self.tr("add_transition"))
        self.design_hint.setText(self.tr("about"))
        self.start_check.setText(self.tr("start_hint")); self.final_check.setText(self.tr("final_hint"))
    
    def navigate(self,key):
        idx={"designer":0,"simulator":1,"table":2,"convert":3}[key]; self.stack.setCurrentIndex(idx)
        if key=="designer": self._refresh_designer()
    
    def reset_sim(self):
        self.current=self.machine.start; self.input_text=self.input_edit.text().strip(); self.input_index=0
        self.path=[self.current] if self.current else []
        self._refresh_all()
    
    def run_sim(self):
        text=self.input_edit.text().strip()
        try:
            if not self.machine.start: raise ValueError("Select a start state first.")
            if self.machine.is_deterministic():
                accepted,path=self.machine.simulate_dfa(text); self.path=path; self.current=path[-1]
            else:
                accepted,paths=self.machine.simulate_nfa(text); self.path=[sorted(x)[0] if len(x)==1 else "{" + ",".join(sorted(x)) + "}" for x in paths]; self.current=self.path[-1] if self.path else self.machine.start
            self.sim_graph.set_automaton(self.machine,self.current,self.path)
            self.current_label.setText(f"{self.tr('current')}: {self.current}")
            self.status_label.setText(f"{self.tr('result')}: {self.tr('accepted') if accepted else self.tr('rejected')}")
            self.path_label.setText(f"{self.tr('path')}: " + " → ".join(self.path))
        except Exception as e: self.show_error(str(e))
    
    def step_sim(self):
        text=self.input_edit.text().strip()
        try:
            if not self.machine.start: raise ValueError("Select a start state first.")
            if self.input_index==0:
                self.current=self.machine.start; self.path=[self.current]
            if self.input_index>=len(text):
                accepted=self.current in self.machine.finals
                self.status_label.setText(f"{self.tr('result')}: {self.tr('accepted') if accepted else self.tr('rejected')}")
                return
            ch=text[self.input_index]
            if self.machine.is_deterministic():
                self.current=self.machine.step_dfa(self.current,ch); self.path.append(self.current)
            else:
                _,paths=self.machine.simulate_nfa(text[:self.input_index+1]); states=paths[-1]
                self.current="{" + ",".join(sorted(states)) + "}" if len(states)!=1 else next(iter(states)); self.path.append(self.current)
            self.input_index+=1
            self.current_label.setText(f"{self.tr('current')}: {self.current}")
            self.path_label.setText(f"{self.tr('path')}: " + " → ".join(self.path))
            self.sim_graph.set_automaton(self.machine,self.current,self.path)
        except Exception as e: self.show_error(str(e))
    
    def convert_nfa(self):
        try:
            if self.machine.is_deterministic():
                raise ValueError("The current machine is already deterministic (DFA).")
            dfa=self.machine.to_dfa(); self.convert_graph.set_automaton(dfa,dfa.start)
            lines=[f"States: {', '.join(dfa.states)}",f"Alphabet: {', '.join(dfa.alphabet)}",f"Start: {dfa.start}",f"Final: {', '.join(sorted(dfa.finals)) or '—'}","", "Transitions:"]
            lines += [f"  {t.source} --{t.symbol}--> {t.target}" for t in dfa.transitions]
            self.convert_info.setPlainText("\n".join(lines))
        except Exception as e: self.show_error(str(e))
    
    def toggle_lang(self):
        self.lang="fa" if self.lang=="en" else "en"; self._refresh_all()
    
    def show_error(self,msg):
        QMessageBox.warning(self,self.tr("error"),msg)

if __name__=="__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion")
    app.setStyleSheet("""
        QMainWindow,QWidget{background:#10131a;color:#e5e7eb;font-family:'Segoe UI';}
        QHeaderView::section{background:#1b202b;color:#cbd5e1;padding:8px;border:0;}
        QTableWidget{background:#12161f;color:#e5e7eb;gridline-color:#303746;border:1px solid #262c38;}
    """)
    win=MainWindow(); win.show(); sys.exit(app.exec())
