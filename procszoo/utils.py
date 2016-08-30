import sys

def warn(text=None, newline=True):
    if text is None:
        text = ''
    if newline:
        sys.stderr.write('%s\n' % text)
    else:
        sys.stderr.write(text)


def printf(text=None, newline=True):
    if text is None:
        text = ''
    if newline:
        sys.stdout.write('%s\n' % text)
    else:
        sys.stdout.write(text)


__all__ = ['warn', 'printf']
