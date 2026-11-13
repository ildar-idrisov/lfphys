from lfphys.i18n import T
MSG = "A brand new label nobody translated"
a = T(MSG)
b = T("Shown " + "concatenated")
c = T(("Open" if True else "Closed"))
d = {"label": "Plain string label nobody translated"}
