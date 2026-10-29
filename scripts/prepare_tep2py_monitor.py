import pathlib,hashlib,difflib
p=pathlib.Path('src/tep/temain_mod.f');orig=p.read_text();s=orig.replace('      K = 1\n','      K = 1\n      XDATA(:,:) = -9999.0D0\n',1)
needle='      CALL CONSHAND\nC\n 1000 CONTINUE'
assert needle in s
s=s.replace(needle,"""      CALL CONSHAND
C     Research-only diagnostic safety monitor, not upstream source.
      IF (XMEAS(7).GE.3000D0.OR.XMEAS(9).GE.175D0.OR.
     1 XMEAS(8).LE.0D0.OR.XMEAS(8).GE.100D0.OR.
     2 XMEAS(12).LE.0D0.OR.XMEAS(12).GE.100D0.OR.
     3 XMEAS(15).LE.0D0.OR.XMEAS(15).GE.100D0.OR.
     4 ANY(XMEAS.NE.XMEAS)) THEN
        PRINT *, 'RESEARCH_SAFETY_STOP', I
        EXIT
      ENDIF
C
 1000 CONTINUE""",1)
p.write_text(s);pathlib.Path('research_patch.diff').write_text(''.join(difflib.unified_diff(orig.splitlines(True),s.splitlines(True),fromfile='upstream',tofile='local-monitor')));print('upstream sha256',hashlib.sha256(orig.encode()).hexdigest());print('patched sha256',hashlib.sha256(s.encode()).hexdigest())
