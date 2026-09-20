import sys, math
from PySide6.QtCore import Qt, QPointF, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
from PySide6.QtWidgets import (
    QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QLineEdit,QTableWidget,QTableWidgetItem,QStackedWidget,QFrame,QMessageBox,
    QHeaderView,QInputDialog,QTextEdit,QSplitter
)
from automata import FiniteAutomaton, Transition
from grammar import ContextFreeGrammar

AUTHOR="Mohammadreza Kazemi — ساخته شده توسط محمدرضا کاظمی"

class GraphView(QWidget):
    state_clicked=Signal(str); changed=Signal()
    def __init__(self,editable=False):
        super().__init__(); self.automaton=None; self.editable=editable; self.positions={}
        self.selected=None; self.dragging=None; self.edge_mode=False; self.edge_source=None
        self.active=None; self.path=[]; self.flow_t=0
        self.setMinimumHeight(420); self.setFocusPolicy(Qt.StrongFocus)
        self.timer=QTimer(self); self.timer.timeout.connect(self._tick); self.timer.start(35)
    def set_automaton(self,a,active=None,path=None):
        self.automaton=a; self.active=active; self.path=path or []
        old=self.positions.copy(); self.positions={}
        if a:
            for i,s in enumerate(a.states):
                self.positions[s]=old.get(s,self._default_pos(i,len(a.states)))
        self.update()
    def _default_pos(self,i,n):
        cx,cy=self.width()/2,self.height()/2
        if n<=1:return QPointF(cx,cy)
        r=min(self.width(),self.height())*.30; ang=-math.pi/2+2*math.pi*i/n
        return QPointF(cx+r*math.cos(ang),cy+r*.72*math.sin(ang))
    def _hit(self,p):
        for s,q in self.positions.items():
            if math.hypot(p.x()-q.x(),p.y()-q.y())<=41:return s
    def mouseDoubleClickEvent(self,e):
        if not self.editable or e.button()!=Qt.LeftButton or self._hit(e.position()):return
        i=0
        while f"q{i}" in self.automaton.states:i+=1
        s=f"q{i}"; self.automaton.add_state(s); self.positions[s]=e.position(); self.selected=s; self.changed.emit(); self.update()
    def mousePressEvent(self,e):
        if not self.editable or e.button()!=Qt.LeftButton:return
        s=self._hit(e.position())
        if self.edge_mode:
            if s:
                if self.edge_source is None:self.edge_source=s; self.selected=s
                else:self._edge(self.edge_source,s); self.edge_source=None
            self.update(); return
        self.selected=s
        if s:self.dragging=s; self.state_clicked.emit(s)
        self.update()
    def mouseMoveEvent(self,e):
        if self.editable and self.dragging and not self.edge_mode:self.positions[self.dragging]=e.position(); self.update()
    def mouseReleaseEvent(self,e):
        if self.dragging:self.dragging=None; self.changed.emit()
    def keyPressEvent(self,e):
        if self.editable and e.key() in (Qt.Key_Delete,Qt.Key_Backspace) and self.selected:
            self.automaton.remove_state(self.selected); self.positions.pop(self.selected,None); self.selected=None; self.changed.emit(); self.update()
    def _edge(self,a,b):
        sym,ok=QInputDialog.getText(self,"Transition",f"{a} → {b}\nSymbol:")
        if ok and sym.strip():
            try:self.automaton.add_transition(a,sym.strip(),b); self.changed.emit()
            except Exception as ex:QMessageBox.warning(self,"Transition",str(ex))
    def _tick(self):self.flow_t=(self.flow_t+.018)%1; self.update()
    def _arrow(self,p,tip,back,pen):
        dx,dy=tip.x()-back.x(),tip.y()-back.y(); d=max(math.hypot(dx,dy),1); ux,uy=dx/d,dy/d
        a=QPointF(tip.x()-ux*11+uy*6,tip.y()-uy*11-ux*6); b=QPointF(tip.x()-ux*11-uy*6,tip.y()-uy*11+ux*6)
        p.drawLine(tip,a);p.drawLine(tip,b)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.fillRect(self.rect(),QColor("#0f131b"))
        if not self.automaton or not self.automaton.states:
            p.setPen(QColor("#64748b"));p.drawText(self.rect(),Qt.AlignCenter,"Double-click to create a state / برای ساخت حالت دوبارکلیک کنید");return
        pairs={}
        for t in self.automaton.transitions:pairs.setdefault((t.source,t.target),[]).append(t.symbol)
        active_pairs=set(zip(self.path,self.path[1:]))
        r=34
        for (a,b),syms in pairs.items():
            if a not in self.positions or b not in self.positions:continue
            q1,q2=self.positions[a],self.positions[b]; active=(a,b) in active_pairs
            pen=QPen(QColor("#9b8cff" if active else "#536174"),3 if active else 2);p.setPen(pen);p.setBrush(Qt.NoBrush)
            if a==b:
                path=QPainterPath(QPointF(q1.x()-28,q1.y()-15));path.cubicTo(q1.x()-80,q1.y()-115,q1.x()+80,q1.y()-115,q1.x()+28,q1.y()-15);p.drawPath(path)
                tip=QPointF(q1.x()+28,q1.y()-15);self._arrow(p,tip,QPointF(tip.x()-3,tip.y()+14),pen);lp=QPointF(q1.x()-10,q1.y()-92)
            else:
                dx,dy=q2.x()-q1.x(),q2.y()-q1.y();d=max(math.hypot(dx,dy),1);ux,uy=dx/d,dy/d
                a1=QPointF(q1.x()+ux*r,q1.y()+uy*r);b1=QPointF(q2.x()-ux*r,q2.y()-uy*r);p.drawLine(a1,b1)
                self._arrow(p,b1,QPointF(b1.x()-ux*12+uy*7,b1.y()-uy*12-ux*7),pen);lp=QPointF((a1.x()+b1.x())/2-10,(a1.y()+b1.y())/2-10)
            p.setPen(QColor("#d7dced"));p.setFont(QFont("Segoe UI",10,QFont.Bold));p.drawText(lp,", ".join(syms))
            if active:
                t=self.flow_t; fp=QPointF(q1.x()+(q2.x()-q1.x())*t,q1.y()+(q2.y()-q1.y())*t) if a!=b else QPointF(q1.x(),q1.y()-70)
                p.setPen(Qt.NoPen);p.setBrush(QBrush(QColor("#d9d3ff")));p.drawEllipse(fp,5,5)
        for s,q in self.positions.items():
            selected=s==self.selected; active=s==self.active
            p.setPen(QPen(QColor("#b5aaff" if selected or active else "#66758a"),3 if selected or active else 2));p.setBrush(QBrush(QColor("#1a202c")));p.drawEllipse(q,r,r)
            if s in self.automaton.finals:p.setBrush(Qt.NoBrush);p.drawEllipse(q,r-6,r-6)
            p.setPen(QColor("#f8fafc"));p.setFont(QFont("Segoe UI",11,QFont.Bold));p.drawText(q.x()-30,q.y()-10,60,20,Qt.AlignCenter,s)
            if s==self.automaton.start:
                pen=QPen(QColor("#66758a"),2);p.setPen(pen);p.drawLine(q.x()-70,q.y(),q.x()-r,q.y());self._arrow(p,QPointF(q.x()-r,q.y()),QPointF(q.x()-r-10,q.y()-5),pen)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.lang="en";self.machine=self.sample();self.current=self.machine.start;self.path=[self.current];self.input_index=0
        self.grammar_text="S -> a A\nA -> b A | ε";self._build();self._texts();self._refresh();self.navigate("home")
    def sample(self):
        return FiniteAutomaton(["q0","q1","q2"],["0","1"],[
            Transition("q0","0","q1"),Transition("q0","1","q0"),Transition("q1","0","q1"),
            Transition("q1","1","q2"),Transition("q2","0","q2"),Transition("q2","1","q0")],"q0",{"q2"})
    def panel(self):
        return "QFrame{background:#151a23;border:1px solid #272f3d;border-radius:12px;} QLabel{color:#aab5c5;} QLineEdit,QTextEdit{background:#0d1118;color:#f4f6fb;border:1px solid #303949;border-radius:7px;padding:8px;} QPushButton{background:#252b39;color:#f7f8fb;border:0;border-radius:7px;padding:9px 13px;} QPushButton:hover{background:#353d50;}"
    def _build(self):
        self.setMinimumSize(1200,780);root=QWidget();self.setCentralWidget(root);out=QHBoxLayout(root);out.setContentsMargins(0,0,0,0)
        side=QFrame();side.setFixedWidth(220);side.setStyleSheet("QFrame{background:#0a0d13;} QPushButton{color:#aeb8c8;background:transparent;border:0;border-radius:8px;padding:13px;text-align:left;font-size:14px;} QPushButton:hover{background:#181d27;color:white;}")
        sl=QVBoxLayout(side);self.logo=QLabel("◉  AUTOMATA\n    LAB");self.logo.setStyleSheet("color:#f8fafc;font-size:17px;font-weight:700;padding:10px;");sl.addWidget(self.logo)
        self.home_btn=QPushButton();self.home_btn.setMinimumHeight(42);self.home_btn.clicked.connect(lambda:self.navigate("home"));sl.addWidget(self.home_btn)
        self.auto_btn=QPushButton();self.auto_btn.setMinimumHeight(42);self.auto_btn.clicked.connect(lambda:self.navigate("designer"));sl.addWidget(self.auto_btn)
        self.grammar_btn=QPushButton();self.grammar_btn.setMinimumHeight(42);self.grammar_btn.clicked.connect(lambda:self.navigate("grammar"));sl.addWidget(self.grammar_btn)
        self.nav=[]
        for k in ("designer","simulator","table","convert"):
            b=QPushButton();b.setMinimumHeight(40);b.clicked.connect(lambda _,x=k:self.navigate(x));self.nav.append((k,b));sl.addWidget(b)
        sl.addStretch();self.lang_btn=QPushButton();self.lang_btn.clicked.connect(self.toggle_lang);sl.addWidget(self.lang_btn)
        sl.addWidget(QLabel(AUTHOR));out.addWidget(side);self.stack=QStackedWidget();out.addWidget(self.stack,1)
        self.stack.addWidget(self._home());self.stack.addWidget(self._designer());self.stack.addWidget(self._simulator());self.stack.addWidget(self._table());self.stack.addWidget(self._convert());self.stack.addWidget(self._grammar())
    def _page(self):
        w=QWidget();l=QVBoxLayout(w);l.setContentsMargins(28,24,28,22);h=QHBoxLayout();title=QLabel();title.setStyleSheet("font-size:25px;font-weight:700;color:#f8fafc;");badge=QLabel();badge.setStyleSheet("background:#242039;color:#bdb6ff;padding:7px 14px;border-radius:8px;");h.addWidget(title);h.addStretch();h.addWidget(badge);l.addLayout(h);return w,l,title,badge
    def _home(self):
        w=QWidget();l=QVBoxLayout(w);l.setContentsMargins(70,55,70,55);title=QLabel("Formal Languages Lab");title.setStyleSheet("font-size:34px;font-weight:800;color:#f8fafc;");sub=QLabel("Automata and Grammar tools for learning, experimentation and demonstration.");sub.setStyleSheet("font-size:15px;color:#8e9aae;");l.addWidget(title);l.addWidget(sub);cards=QHBoxLayout()
        for name,desc,key in [("◉  Automata Lab","DFA/NFA designer, simulator, transition table and NFA → DFA.","designer"),("⌘  Grammar Lab","Grammar editor, validation, parsing, parse tree, derivations, FIRST/FOLLOW and LL(1).","grammar")]:
            c=QFrame();c.setStyleSheet(self.panel());cl=QVBoxLayout(c);t=QLabel(name);t.setStyleSheet("font-size:23px;font-weight:700;color:#f8fafc;");d=QLabel(desc);d.setWordWrap(True);d.setStyleSheet("color:#8e9aae;font-size:13px;");b=QPushButton("Open");b.setMinimumHeight(52);b.clicked.connect(lambda _,x=key:self.navigate(x));cl.addWidget(t);cl.addWidget(d);cl.addStretch();cl.addWidget(b);cards.addWidget(c)
        l.addLayout(cards);l.addStretch();a=QLabel(AUTHOR);a.setAlignment(Qt.AlignCenter);a.setStyleSheet("color:#596579;");l.addWidget(a);return w
    def _designer(self):
        w,l,self.dtitle,self.dbadge=self._page();bar=QFrame();bar.setStyleSheet(self.panel());bl=QHBoxLayout(bar)
        self.add_btn=QPushButton();self.edge_btn=QPushButton();self.edge_btn.setCheckable(True);self.start_btn=QPushButton();self.final_btn=QPushButton();self.del_btn=QPushButton()
        self.add_btn.clicked.connect(self.create_state);self.edge_btn.toggled.connect(lambda x:self._edge_mode(x));self.start_btn.clicked.connect(self.set_start);self.final_btn.clicked.connect(self.toggle_final);self.del_btn.clicked.connect(self.delete_state)
        for b in (self.add_btn,self.edge_btn,self.start_btn,self.final_btn,self.del_btn):bl.addWidget(b)
        l.addWidget(bar);self.design_graph=GraphView(True);self.design_graph.state_clicked.connect(lambda s:self._select(s));self.design_graph.changed.connect(self._refresh);l.addWidget(self.design_graph,1);self.hint=QLabel();l.addWidget(self.hint);return w
    def _simulator(self):
        w,l,self.stitle,self.sbadge=self._page();self.sim_graph=GraphView();l.addWidget(self.sim_graph,1);bar=QFrame();bar.setStyleSheet(self.panel());bl=QHBoxLayout(bar);self.input=QLineEdit("0101");self.run_btn=QPushButton();self.step_btn=QPushButton();self.reset_btn=QPushButton();self.current_lbl=QLabel();self.status=QLabel()
        self.run_btn.clicked.connect(self.run_sim);self.step_btn.clicked.connect(self.step_sim);self.reset_btn.clicked.connect(self.reset_sim)
        for x in (self.input,self.run_btn,self.step_btn,self.reset_btn,self.current_lbl,self.status):bl.addWidget(x)
        l.addWidget(bar);self.path_lbl=QLabel();l.addWidget(self.path_lbl);return w
    def _table(self):
        w,l,self.ttitle,self.tbadge=self._page();self.tw=QTableWidget();self.tw.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);l.addWidget(self.tw);return w
    def _convert(self):
        w,l,self.ctitle,self.cbadge=self._page();self.convert_btn=QPushButton();self.convert_btn.clicked.connect(self.convert_nfa);l.addWidget(self.convert_btn);self.cg=GraphView();l.addWidget(self.cg,1);self.cinfo=QTextEdit();self.cinfo.setReadOnly(True);self.cinfo.setMaximumHeight(170);l.addWidget(self.cinfo);return w
    def _grammar(self):
        w,l,self.gtitle,self.gbadge=self._page()
        w.setStyleSheet(self.panel())
        toolbar=QFrame();toolbar.setStyleSheet(self.panel());tb=QHBoxLayout(toolbar)
        self.gback=QPushButton();self.ganalyze=QPushButton();self.gleft=QPushButton();self.gfactor=QPushButton();self.gll1=QPushButton()
        self.gback.clicked.connect(lambda:self.navigate("designer"));self.ganalyze.clicked.connect(self.grammar_analyze);self.gleft.clicked.connect(self.grammar_left);self.gfactor.clicked.connect(self.grammar_factor);self.gll1.clicked.connect(self.grammar_ll1)
        for b in (self.gback,self.ganalyze,self.gleft,self.gfactor,self.gll1):b.setMinimumHeight(40);tb.addWidget(b)
        l.addWidget(toolbar)

        self.grammar_info=QLabel()
        self.grammar_info.setStyleSheet("color:#8793a7;padding:5px 2px;");l.addWidget(self.grammar_info)

        split=QSplitter(Qt.Horizontal)
        left=QFrame();left.setStyleSheet(self.panel());ll=QVBoxLayout(left)
        head=QHBoxLayout();self.grammar_editor_label=QLabel();self.grammar_editor_label.setStyleSheet("font-size:17px;font-weight:700;color:#f8fafc;");example=QPushButton();self.grammar_example_btn=example;example.clicked.connect(lambda:self.geditor.setPlainText("E -> E + T | T\\nT -> T * F | F\\nF -> ( E ) | id"));head.addWidget(self.grammar_editor_label);head.addStretch();head.addWidget(example);ll.addLayout(head)
        self.geditor=QTextEdit(self.grammar_text);self.geditor.setStyleSheet("QTextEdit{font-family:'Consolas';font-size:14px;background:#0b1017;border:1px solid #303949;border-radius:9px;padding:10px;color:#e8edf5;}");ll.addWidget(self.geditor,1)
        ll.addWidget(QLabel("Input string"));self.ginput=QLineEdit("abb");self.ginput.setMinimumHeight(40);ll.addWidget(self.ginput)
        split.addWidget(left)

        mid=QFrame();mid.setStyleSheet(self.panel());ml=QVBoxLayout(mid)
        self.grammar_tree_label=QLabel();self.grammar_tree_label.setStyleSheet("font-size:17px;font-weight:700;color:#f8fafc;");ml.addWidget(self.grammar_tree_label)
        self.gtree=QTextEdit();self.gtree.setReadOnly(True);self.gtree.setStyleSheet("QTextEdit{font-family:'Consolas';font-size:14px;background:#0b1017;border:1px solid #303949;border-radius:9px;color:#d9e1ef;padding:12px;}");ml.addWidget(self.gtree,1)
        self.grammar_derivation_label=QLabel();self.grammar_derivation_label.setStyleSheet("font-size:17px;font-weight:700;color:#f8fafc;");ml.addWidget(self.grammar_derivation_label)
        self.gder=QTextEdit();self.gder.setReadOnly(True);self.gder.setMaximumHeight(180);ml.addWidget(self.gder)
        split.addWidget(mid)

        right=QFrame();right.setStyleSheet(self.panel());rl=QVBoxLayout(right)
        tabs=QHBoxLayout()
        self.gtab_buttons=[]
        for txt,key in (("Analysis","analysis"),("FIRST / FOLLOW","first_follow"),("LL(1)","ll1")):
            q=QPushButton();q.setObjectName("grammar_tab_"+key);q.setMinimumHeight(34);self.gtab_buttons.append((key,q));tabs.addWidget(q)
        rl.addLayout(tabs)
        self.ganalysis=QTextEdit();self.ganalysis.setReadOnly(True);self.ganalysis.setStyleSheet("QTextEdit{font-family:'Consolas';background:#0b1017;border:1px solid #303949;border-radius:9px;color:#d9e1ef;padding:12px;}");rl.addWidget(self.ganalysis,1)
        split.addWidget(right)
        split.setSizes([430,430,360])
        l.addWidget(split,1)
        return w

    def _edge_mode(self,on):self.design_graph.edge_mode=on;self.edge_btn.setText("✓ Edge mode" if on else "Draw Transition")
    def _select(self,s):self.design_graph.selected=s;self._refresh()
    def create_state(self):
        i=0
        while f"q{i}" in self.machine.states:i+=1
        self.machine.add_state(f"q{i}");self.design_graph.selected=f"q{i}";self._refresh()
    def set_start(self):
        if self.design_graph.selected:self.machine.start=self.design_graph.selected;self.current=self.machine.start;self.path=[self.current];self._refresh()
    def toggle_final(self):
        s=self.design_graph.selected
        if s:
            self.machine.finals.symmetric_difference_update({s});self._refresh()
    def delete_state(self):
        s=self.design_graph.selected
        if s:self.machine.remove_state(s);self.design_graph.selected=None;self._refresh()
    def _refresh(self):
        self._texts();self.design_graph.set_automaton(self.machine,self.current,self.path);self.sim_graph.set_automaton(self.machine,self.current,self.path);self._table_refresh();self.current_lbl.setText(f"{self.tr('current')}: {self.current or '—'}");self.status.setText(f"{self.tr('result')}: {self.tr('ready')}");self.path_lbl.setText(f"{self.tr('path')}: {' → '.join(self.path)}")
    def _table_refresh(self):
        self.tw.setColumnCount(len(self.machine.alphabet)+1);self.tw.setHorizontalHeaderLabels([self.tr("state")]+self.machine.alphabet);self.tw.setRowCount(len(self.machine.states))
        for r,s in enumerate(self.machine.states):
            self.tw.setItem(r,0,QTableWidgetItem(("→ " if s==self.machine.start else "")+("* " if s in self.machine.finals else "")+s))
            for c,a in enumerate(self.machine.alphabet,1):self.tw.setItem(r,c,QTableWidgetItem(", ".join(sorted(self.machine.destinations(s,a))) or "—"))
    def run_sim(self):
        try:
            text=self.input.text().strip()
            ok,path=self.machine.simulate_dfa(text) if self.machine.is_deterministic() else self.machine.simulate_nfa(text)
            if self.machine.is_deterministic():self.path=path;self.current=path[-1]
            else:self.path=["{"+",".join(sorted(x))+"}" for x in path];self.current=self.path[-1]
            self.sim_graph.set_automaton(self.machine,self.current,self.path);self.status.setText(f"{self.tr('result')}: {self.tr('accepted') if ok else self.tr('rejected')}");self.path_lbl.setText(f"{self.tr('path')}: {' → '.join(self.path)}")
        except Exception as ex:QMessageBox.warning(self,"Error",str(ex))
    def step_sim(self):
        try:
            text=self.input.text().strip()
            if self.input_index==0:self.current=self.machine.start;self.path=[self.current]
            if self.input_index>=len(text):self.status.setText(f"{self.tr('result')}: {self.tr('accepted') if self.current in self.machine.finals else self.tr('rejected')}");return
            self.current=self.machine.step_dfa(self.current,text[self.input_index]);self.input_index+=1;self.path.append(self.current);self.sim_graph.set_automaton(self.machine,self.current,self.path);self.current_lbl.setText(f"{self.tr('current')}: {self.current}")
        except Exception as ex:QMessageBox.warning(self,"Error",str(ex))
    def reset_sim(self):self.current=self.machine.start;self.input_index=0;self.path=[self.current];self._refresh()
    def convert_nfa(self):
        try:
            d=self.machine.to_dfa();self.cg.set_automaton(d,d.start);self.cinfo.setPlainText("\n".join(["DFA created by subset construction","",f"States: {', '.join(d.states)}",f"Start: {d.start}",f"Final: {', '.join(sorted(d.finals)) or '—'}",""]+[f"{t.source} --{t.symbol}--> {t.target}" for t in d.transitions]))
        except Exception as ex:QMessageBox.warning(self,"Conversion",str(ex))
    def grammar_analyze(self):
        try:
            g=ContextFreeGrammar("S").parse(self.geditor.toPlainText());errs=g.validate();first=g.first_sets();follow=g.follow_sets();ok,tree,toks=g.parse_string(self.ginput.text().strip())
            ll,conf=g.ll1_table();lines=[("Grammar is valid ✓" if not errs else "Grammar errors:")]+errs+[f"Classification: {g.classification()}",f"Productions: {len(g.productions)}","", "FIRST:"]
            lines += [f"FIRST({n}) = {{ {', '.join(sorted(first[n]))} }}" for n in sorted(first)]+["","FOLLOW:"]
            lines += [f"FOLLOW({n}) = {{ {', '.join(sorted(follow[n]))} }}" for n in sorted(follow)]+["",f"LL(1): {'Yes' if not conf else 'No — conflicts detected'}", "","String: "+("Accepted ✓" if ok else "Rejected ✕")]
            self.ganalysis.setPlainText("\n".join(lines));self.gtree.setPlainText(self.format_tree(tree) if ok else "—");self.gder.setPlainText("\n".join(g.leftmost_derivation(tree)) if ok else "—")
        except Exception as ex:QMessageBox.warning(self,"Grammar Error",str(ex))
    def grammar_left(self):
        try:g=ContextFreeGrammar("S").parse(self.geditor.toPlainText());g.remove_left_recursion();self.geditor.setPlainText(g.text());self.grammar_analyze()
        except Exception as ex:QMessageBox.warning(self,"Grammar Error",str(ex))
    def grammar_factor(self):
        try:g=ContextFreeGrammar("S").parse(self.geditor.toPlainText());g.left_factor();self.geditor.setPlainText(g.text());self.grammar_analyze()
        except Exception as ex:QMessageBox.warning(self,"Grammar Error",str(ex))
    def grammar_ll1(self):
        try:g=ContextFreeGrammar("S").parse(self.geditor.toPlainText());tab,conf=g.ll1_table();lines=["LL(1) Parsing Table","" if not conf else "CONFLICTS:"]+[str(x) for x in conf]
        except Exception as ex:QMessageBox.warning(self,"Grammar Error",str(ex));return
        for k,v in sorted(tab.items()):lines.append(f"{k[0]}, {k[1]} → "+ " | ".join(v));self.ganalysis.setPlainText("\n".join(lines))
    def format_tree(self,t,indent=""):
        if not t:return ""
        if t[0]=="token":return indent+t[1]
        return "\n".join([indent+t[1]]+[self.format_tree(c,indent+"  ") for c in t[2]])
    def navigate(self,k):self.stack.setCurrentIndex({"home":0,"designer":1,"simulator":2,"table":3,"convert":4,"grammar":5}[k])
    def toggle_lang(self):self.lang="fa" if self.lang=="en" else "en";self.setLayoutDirection(Qt.RightToLeft if self.lang=="fa" else Qt.LeftToRight);self._texts()
    def tr(self,k):
        fa={"home":"خانه","automata":"بخش اتوماتا","grammar":"بخش گرامر","designer":"طراحی ماشین","simulator":"شبیه‌ساز","table":"جدول انتقال","convert":"NFA → DFA","current":"حالت فعلی","result":"نتیجه","ready":"آماده","run":"اجرا","step":"مرحله بعد","reset":"بازنشانی","state":"حالت","path":"مسیر","accepted":"پذیرفته شد ✓","rejected":"رد شد ✕"}
        en={"home":"Home","automata":"Automata Lab","grammar":"Grammar Lab","designer":"Designer","simulator":"Simulator","table":"Transition Table","convert":"NFA → DFA","current":"Current","result":"Result","ready":"Ready","run":"Run","step":"Step","reset":"Reset","state":"State","path":"Path","accepted":"Accepted ✓","rejected":"Rejected ✕"}
        return (fa if self.lang=="fa" else en).get(k,k)
    def _texts(self):
        self.home_btn.setText(self.tr("home"));self.auto_btn.setText(self.tr("automata"));self.grammar_btn.setText(self.tr("grammar"))
        for k,b in self.nav:b.setText(self.tr(k))
        self.lang_btn.setText("فارسی / English")
        self.dtitle.setText(self.tr("designer"));self.stitle.setText(self.tr("simulator"));self.ttitle.setText(self.tr("table"));self.ctitle.setText(self.tr("convert"));self.gtitle.setText("آزمایشگاه گرامر" if self.lang=="fa" else "Grammar Lab")
        self.dbadge.setText("DFA" if self.machine.is_deterministic() else "NFA");self.sbadge.setText(self.dbadge.text());self.tbadge.setText(self.dbadge.text());self.cbadge.setText(self.dbadge.text());self.gbadge.setText("CFG")
        self.add_btn.setText("+ حالت" if self.lang=="fa" else "+ State");self.edge_btn.setText(("✓ حالت رسم" if self.lang=="fa" else "✓ Edge mode") if self.edge_btn.isChecked() else ("رسم انتقال" if self.lang=="fa" else "Draw Transition"));self.start_btn.setText("شروع" if self.lang=="fa" else "Set Start");self.final_btn.setText("نهایی" if self.lang=="fa" else "Toggle Final");self.del_btn.setText("حذف حالت" if self.lang=="fa" else "Delete State");self.hint.setText("دوبارکلیک = حالت جدید • کشیدن = جابه‌جایی • رسم انتقال = اتصال دو حالت" if self.lang=="fa" else "Double-click = new state • Drag = move • Draw Transition = connect states")
        self.run_btn.setText(self.tr("run"));self.step_btn.setText(self.tr("step"));self.reset_btn.setText(self.tr("reset"));self.convert_btn.setText("تبدیل NFA به DFA" if self.lang=="fa" else "Convert NFA to DFA")
        self.gback.setText("← بخش اتوماتا" if self.lang=="fa" else "← Automata Lab")
        self.ganalyze.setText("▶ تحلیل و آزمون" if self.lang=="fa" else "▶ Analyze & Test")
        self.gleft.setText("↻ حذف بازگشت چپ" if self.lang=="fa" else "↻ Remove Left Recursion")
        self.gfactor.setText("⇥ فاکتورگیری چپ" if self.lang=="fa" else "⇥ Left Factor")
        self.gll1.setText("▦ جدول LL(1)" if self.lang=="fa" else "▦ LL(1) Table")
        self.grammar_editor_label.setText("ویرایشگر گرامر" if self.lang=="fa" else "Grammar Editor")
        self.grammar_example_btn.setText("بارگذاری مثال" if self.lang=="fa" else "Load Example")
        self.grammar_info.setText("تولیدها را مثل  S → a A | ε  بنویسید  •  رشته را پایین وارد کنید  •  برای ساخت درخت و گزارش، تحلیل را بزنید" if self.lang=="fa" else "Write productions like  S → a A | ε  •  Test a string below  •  Analyze to build the tree and grammar report")
        self.grammar_tree_label.setText("درخت تجزیه" if self.lang=="fa" else "Parse Tree")
        self.grammar_derivation_label.setText("اشتقاق" if self.lang=="fa" else "Derivation")
        for key,q in self.gtab_buttons:
            q.setText({"analysis":"تحلیل","first_follow":"FIRST / FOLLOW","ll1":"LL(1)"}[key] if self.lang=="fa" else {"analysis":"Analysis","first_follow":"FIRST / FOLLOW","ll1":"LL(1)"}[key])
        self.ginput.setPlaceholderText("رشته ورودی" if self.lang=="fa" else "Input string")
if __name__=="__main__":
    app=QApplication(sys.argv);app.setStyle("Fusion");app.setStyleSheet("QMainWindow,QWidget{background:#10141c;color:#e5e7eb;font-family:'Segoe UI';} QHeaderView::section{background:#1b212c;color:#cbd5e1;padding:8px;border:0;} QTableWidget{background:#121720;color:#e5e7eb;gridline-color:#303746;border:1px solid #272f3d;}")
    win=MainWindow();win.show();sys.exit(app.exec())
