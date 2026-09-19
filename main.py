import sys
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QStackedWidget,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsTextItem, QFrame, QMessageBox, QComboBox
)

AUTHOR = "Mohammadreza Kazemi — ساخته شده توسط محمدرضا کاظمی"

STRINGS = {
    "en": {
        "title":"Automata Simulator","designer":"Designer","simulator":"Simulator",
        "table":"Transition Table","convert":"NFA → DFA","language":"Language",
        "input":"Input String","run":"Run","step":"Step","reset":"Reset",
        "current":"Current State","status":"Status","accepted":"String Accepted ✓",
        "rejected":"String Rejected ✕","ready":"Ready","state":"State",
        "zero":"0","one":"1","created":"Created by Mohammadreza Kazemi"
    },
    "fa": {
        "title":"شبیه‌ساز ماشین متناهی","designer":"طراح ماشین","simulator":"شبیه‌ساز",
        "table":"جدول انتقال","convert":"تبدیل NFA به DFA","language":"زبان",
        "input":"رشته ورودی","run":"اجرا","step":"مرحله بعد","reset":"بازنشانی",
        "current":"حالت فعلی","status":"وضعیت","accepted":"رشته پذیرفته شد ✓",
        "rejected":"رشته رد شد ✕","ready":"آماده","state":"حالت",
        "zero":"۰","one":"۱","created":"ساخته شده توسط محمدرضا کاظمی"
    }
}

class GraphView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(self.renderHints())
        self.setStyleSheet("background:#10131a;border:0;")
        self.draw_dfa("q0")

    def draw_dfa(self, active="q0"):
        s=self.scene(); s.clear()
        pen=QPen(QColor("#64748b"),3)
        active_pen=QPen(QColor("#8b7cff"),4)
        positions={"q0":QPointF(130,190),"q1":QPointF(360,110),"q2":QPointF(590,190)}
        edges=[("q0","q1","0"),("q1","q2","1"),("q0","q2","1"),("q1","q1","0"),("q2","q2","0,1")]
        for a,b,label in edges:
            p1,p2=positions[a],positions[b]
            if a==b:
                path=QPainterPath(QPointF(p1.x()-25,p1.y()-25))
                path.cubicTo(p1.x()-65,p1.y()-95,p1.x()+65,p1.y()-95,p1.x()+25,p1.y()-25)
                item=s.addPath(path, active_pen if a==active else pen)
                t=s.addText(label,QFont("Segoe UI",11)); t.setDefaultTextColor(QColor("#cbd5e1")); t.setPos(p1.x()-8,p1.y()-105)
                continue
            line=s.addLine(p1.x()+28,p1.y(),p2.x()-28,p2.y(),active_pen if a==active else pen)
            dx=p2.x()-p1.x(); dy=p2.y()-p1.y(); length=max((dx*dx+dy*dy)**0.5,1)
            ux,uy=dx/length,dy/length
            ah=10
            s.addLine(p2.x()-28,p2.y(),p2.x()-28-ah*ux+ah*uy,p2.y()-ah*uy-ah*ux,active_pen if a==active else pen)
            s.addLine(p2.x()-28,p2.y(),p2.x()-28-ah*ux-ah*uy,p2.y()-ah*uy+ah*ux,active_pen if a==active else pen)
            t=s.addText(label,QFont("Segoe UI",11)); t.setDefaultTextColor(QColor("#cbd5e1")); t.setPos((p1.x()+p2.x())/2-5,(p1.y()+p2.y())/2-22)
        for name,p in positions.items():
            r=32; item=s.addEllipse(p.x()-r,p.y()-r,2*r,2*r,QPen(QColor("#8b7cff") if name==active else "#64748b",3),QBrush(QColor("#171b25")))
            if name=="q2":
                s.addEllipse(p.x()-r+6,p.y()-r+6,2*r-12,2*r-12,QPen(QColor("#64748b"),2))
            t=s.addText(name,QFont("Segoe UI",12,QFont.Bold)); t.setDefaultTextColor(QColor("#f8fafc")); t.setPos(p.x()-10,p.y()-11)
        start=s.addLine(55,190,98,190,QPen(QColor("#64748b"),3))
        s.addLine(98,190,88,184,QPen(QColor("#64748b"),3)); s.addLine(98,190,88,196,QPen(QColor("#64748b"),3))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.lang="en"; self.index=0; self.state="q0"; self.text=""
        self.setMinimumSize(1100,700); self.build()

    def tr(self,k): return STRINGS[self.lang][k]

    def build(self):
        self.setWindowTitle(self.tr("title"))
        root=QWidget(); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(0,0,0,0)
        self.sidebar=QFrame(); self.sidebar.setFixedWidth(210); self.sidebar.setStyleSheet("QFrame{background:#0b0e14;} QPushButton{color:#aab4c3;background:transparent;border:0;padding:13px;text-align:left;font-size:14px;} QPushButton:hover{background:#171b25;color:white;}")
        sl=QVBoxLayout(self.sidebar); sl.setContentsMargins(15,20,15,15)
        logo=QLabel("◉  AUTOMATA\n    SIMULATOR"); logo.setStyleSheet("color:#f8fafc;font-size:17px;font-weight:700;padding:10px;"); sl.addWidget(logo)
        self.buttons=[]
        for key in ["designer","simulator","table","convert"]:
            b=QPushButton(self.tr(key)); b.clicked.connect(lambda _,k=key:self.navigate(k)); self.buttons.append((key,b)); sl.addWidget(b)
        sl.addStretch(); self.lang_btn=QPushButton("فارسی / English"); self.lang_btn.clicked.connect(self.toggle_lang); sl.addWidget(self.lang_btn)
        author=QLabel(self.tr("created")); author.setWordWrap(True); author.setStyleSheet("color:#64748b;font-size:11px;padding:10px;"); sl.addWidget(author); self.author=author
        outer.addWidget(self.sidebar)
        self.stack=QStackedWidget(); outer.addWidget(self.stack,1)
        self.stack.addWidget(self.sim_page()); self.stack.addWidget(self.table_page()); self.stack.addWidget(self.simple_page("NFA → DFA"))
        self.stack.setCurrentIndex(0)

    def base(self,title):
        w=QWidget(); lay=QVBoxLayout(w); lay.setContentsMargins(28,25,28,20)
        h=QHBoxLayout(); lab=QLabel(title); lab.setStyleSheet("font-size:25px;font-weight:700;color:#f8fafc;"); h.addWidget(lab); h.addStretch()
        typ=QLabel("DFA"); typ.setStyleSheet("background:#242039;color:#b9b1ff;padding:7px 14px;border-radius:8px;"); h.addWidget(typ); lay.addLayout(h); return w,lay

    def sim_page(self):
        w,lay=self.base(self.tr("simulator")); self.graph=GraphView(); lay.addWidget(self.graph,1)
        panel=QFrame(); panel.setStyleSheet("QFrame{background:#151923;border:1px solid #262c38;border-radius:10px;} QLabel{color:#aab4c3;} QLineEdit{background:#0f1218;color:#f8fafc;border:1px solid #303746;border-radius:7px;padding:9px;} QPushButton{background:#25283a;color:#f8fafc;border:0;border-radius:7px;padding:9px 18px;} QPushButton:hover{background:#353956;}")
        pl=QHBoxLayout(panel); pl.addWidget(QLabel(self.tr("input")+":")); self.input=QLineEdit("0101"); pl.addWidget(self.input,1)
        for k in ["run","step","reset"]:
            b=QPushButton(self.tr(k)); b.clicked.connect(lambda _,x=k:self.action(x)); pl.addWidget(b)
        self.current=QLabel(f"{self.tr('current')}: q0"); self.status=QLabel(f"{self.tr('status')}: {self.tr('ready')}"); pl.addWidget(self.current); pl.addWidget(self.status); lay.addWidget(panel)
        return w

    def table_page(self):
        w,lay=self.base(self.tr("table")); table=QTableWidget(3,3); table.setHorizontalHeaderLabels(["State","0","1"]); data=[["→ q0","q1","q0"],["q1","q1","q2"],["* q2","q2","q0"]]
        for i,row in enumerate(data):
            for j,v in enumerate(row): table.setItem(i,j,QTableWidgetItem(v))
        table.setStyleSheet("QTableWidget{background:#12161f;color:#e5e7eb;gridline-color:#303746;} QHeaderView::section{background:#1b202b;color:#cbd5e1;padding:8px;}")
        lay.addWidget(table); return w

    def simple_page(self,title):
        w,lay=self.base(title); x=QLabel("NFA → DFA\n\nSubset-construction workspace — next project module."); x.setStyleSheet("color:#94a3b8;font-size:18px;"); lay.addWidget(x); lay.addStretch(); return w

    def navigate(self,key):
        self.stack.setCurrentIndex({"simulator":0,"designer":0,"table":1,"convert":2}[key])

    def action(self,a):
        if a=="reset": self.index=0; self.state="q0"
        elif a=="step":
            s=self.input.text().strip(); self.index=min(self.index+1,len(s))
            if self.index and s[self.index-1]=="0": self.state={"q0":"q1","q1":"q1","q2":"q2"}[self.state]
            elif self.index: self.state={"q0":"q0","q1":"q2","q2":"q0"}[self.state]
        elif a=="run":
            self.index=0; self.state="q0"; s=self.input.text().strip()
            for ch in s:
                if ch not in "01": self.status.setText(f"{self.tr('status')}: Invalid input"); return
                self.state=({"q0":"q1","q1":"q1","q2":"q2"} if ch=="0" else {"q0":"q0","q1":"q2","q2":"q0"})[self.state]
            self.status.setText(f"{self.tr('status')}: {self.tr('accepted') if self.state=='q2' else self.tr('rejected')}")
            self.index=len(s)
        self.graph.draw_dfa(self.state); self.current.setText(f"{self.tr('current')}: {self.state}")
        if a!="run": self.status.setText(f"{self.tr('status')}: {self.tr('ready')}")

    def toggle_lang(self):
        self.lang="fa" if self.lang=="en" else "en"; self.rebuild_text()

    def rebuild_text(self):
        for key,b in self.buttons: b.setText(self.tr(key))
        self.author.setText(self.tr("created")); self.setWindowTitle(self.tr("title"))
        self.input.parentWidget().layout().itemAt(0).widget().setText(self.tr("input")+":")
        self.current.setText(f"{self.tr('current')}: {self.state}")

if __name__=="__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion")
    app.setStyleSheet("QMainWindow{background:#10131a;} QWidget{font-family:'Segoe UI';}")
    win=MainWindow(); win.show(); sys.exit(app.exec())
