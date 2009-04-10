TAB = '  '#'    '
common_core          = ['class', 'id', 'title']
common_international = ['xml:lang', 'dir']
common_event         = ['onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']
common_style         = ['style']
common               = common_core + common_international + common_event + common_style

class html_tag(object):
    child      = None
    is_single  = False
    is_pretty  = True
    #Does not insert newlines on all children if True (recursive attribute)
    is_inline  = False
    #Allows missing required attributes and invalid attributes if True
    is_invalid = False
    valid      = []
    required   = []
    default    = {}
    
    def __init__(self, *args, **kwargs):
        self.attributes = {}
        self.children   = []
        
        for i in args:
            self.add(i)
        
        for attribute, value in kwargs.items():
            if attribute == '__inline':
                self.is_inline = value
                continue
            elif attribute == '__invalid':
                self.is_invalid = value
                continue
            
            #Workaround for python's reserved words
            if attribute[0] == '_': attribute = attribute[1:]
            #Workaround for inability to use colon in python keywords
            attribute = attribute.replace('_', ':')
            
            if not attribute in self.valid and not self.is_invalid:
                raise AttributeError("Invalid attribute '%s'." % attribute)
            
            self.attributes[attribute] = value
        
        #Check for missing required attributes
        missing = set(self.required) - set(self.attributes)
        
        #Attempt to assign default values to missing required attributes
        for attribute in missing:
            if attribute in self.default:
                self.attributes[attribute] = self.default[attribute]
                
        #Recheck for missing attributes
        missing = set(self.required) - set(self.attributes)
        
        if missing and not self.is_invalid:
            raise AttributeError("Missing required attribute(s): '%s'" % ','.join(missing))
        
    def add(self, *args):
        for obj in args:
            if self.child and not isinstance(obj, self.child):
                obj = self.child(obj)
            self.children.append(obj)
            if isinstance(obj, html_tag):
                obj.parent = self
        return args[-1]
    
    def tag(self, tag):
        if isinstance(tag, str): tag = globals()[tag]
        return [i for i in self.children if type(i) is tag]
    
    def get(self, attr, value, type=object):
        result = []
        for i in self.children:
            if not isinstance(i, html_tag): continue
            if (not attr or i.attributes.get(attr, None) == value) and isinstance(i, type):
                result.append(i)
            result.extend(i.get(attr, value, type))
        return result
    
    def __getattr__(self, attr):
        try: return self.attributes[attr]
        except KeyError: raise AttributeError
    
    def __setitem__(self, attr, value):
        self.attributes[attr] = value
    
    def __add__(self, obj):
        self.add(obj)
        return self
    
    def __iadd__(self, obj):
        self.add(obj)
        return self
    
    def render(self, n=1, do_inline=False):
        inline = self.is_inline or do_inline
        
        if isinstance(self, dummy):
            #Ignore dummy element just used to set up blocks in methods
            return self.render_children(n, inline)
        elif isinstance(self, comment):
            #No easy way to render a comment except with a special case
            separator = ' '
            if 'separator' in self.attributes:
                separator = self.attributes['separator']
                #For multiline comments:
                # comment("I'm on my own line!", separator='\n')
                #For IE's "if" statement comments:
                # comment("[lt IE6]>", p("Upgrade your browser."), "<![endif]", separator='')
            return "<!--%s%s%s-->" % (separator, self.render_children(n, inline), separator)
        
        s = '<'
        
        #Workaround for python keywords
        if type(self).__name__[0] == "_":
            name = type(self).__name__[1:]
        else:
            name = type(self).__name__
        s += name
        
        for k, v in self.attributes.items():
            s += ' %s="%s"' % (k, str(v))
        
        if self.is_single and not self.children:
            s += ' />'
        else:
            s += '>'
            s += self.render_children(n, inline)
            
            # if there are no children, or only 1 child that is not an html element, do not add tabs and newlines
            no_children = self.is_pretty and self.children and (not (len(self.children) == 1 and not isinstance(self.children[0], html_tag)))
            
            if no_children and not inline:
                s += '\n'
                s += TAB*(n-1)
            s += '</'
            s += name
            s += '>'
        return s
        
    def render_children(self, n=1, do_inline=False):
        s = ''
        for i in self.children:
            if isinstance(i, html_tag):
                if not do_inline and self.is_pretty:
                    s += '\n'
                    s += TAB*n
                s += i.render(n+1, do_inline)
            else:
                s += str(i)
        return s
    
    def __str__(self):
        return self.render()

class single (html_tag): is_single = True
class ugly   (html_tag): is_pretty = False
class dummy  (html_tag): pass
class comment(html_tag): valid = ['separator']

################################################################################
########################## XHTML 1.1 Tag Specification #########################
################################################################################
#Structure & Header
class base (single):
    valid    = ['href']
    required = ['href']
class body (html_tag): valid = ['onload', 'onunload'] + common
class head (html_tag): valid = ['profile'] + common_international
class html (html_tag):
    valid    = ['xmlns', 'xml:lang', 'xmlns:xsi', 'xsi:schemaLocation', 'version'] + common_international
    required = ['xmlns']
    default  = {'xmlns': 'http://www.w3.org/1999/xhtml'}
class link (single):   valid = ['href', 'media', 'type', 'charset', 'hreflang', 'rel', 'rev'] + common
class meta (single):
    valid    = ['content', 'name', 'http-equiv', 'scheme'] + common_international
    required = ['name']
class script(ugly):
    valid    = ['src', 'type', 'charset', 'defer', 'xml:space'] + common
    required = ['type']
class style(ugly):
    valid    = ['media', 'title', 'type', 'xml:space'] + common_international
    required = ['type']
class title(html_tag): valid = common_international

#Block elements
class address   (html_tag): valid = common
class blockquote(html_tag): valid = ['cite'] + common
class _del      (html_tag): valid = ['cite', 'datetime'] + common
class div       (html_tag): valid = common
class dl        (html_tag): valid = common
class fieldset  (html_tag): valid = common
class form      (html_tag): valid = ['action', 'method', 'accept', 'accept-charsets', 'enctype', 'onreset', 'onsubmit'] + common
class h1        (html_tag): valid = common
class h2        (html_tag): valid = common
class h3        (html_tag): valid = common
class h4        (html_tag): valid = common
class h5        (html_tag): valid = common
class h6        (html_tag): valid = common
class hr        (single):   valid = common
class ins       (html_tag): valid = ['cite', 'datetime'] + common
class noscript  (html_tag): valid = common
class ol        (html_tag): valid = common
class p         (html_tag): valid = common
class pre       (ugly):     valid = ['xml:space'] + common
class table     (html_tag): valid = ['border', 'cellpadding', 'cellspacing', 'summary', 'width', 'frame', 'rules'] + common
class ul        (html_tag): valid = common

#Inline elements
class a       (html_tag): valid = ['href', 'accesskey', 'charset', 'choords', 'hreflang', 'onblur', 'onfocus', 'rel', 'rev', 'shape', 'tabindex', 'type'] + common
class abbr    (html_tag): valid = common
class acronym (html_tag): valid = common
class b       (html_tag): valid = common
class bdo     (html_tag): valid = ['dir'] + common
class big     (html_tag): valid = common
class br      (single):   valid = common
class button  (html_tag): valid = ['name', 'type', 'value', 'accesskey', 'disabled', 'onblur', 'onfocus', 'tabindex'] + common
class cite    (html_tag): valid = common
class code    (ugly):     valid = common
class dfn     (html_tag): valid = common
class em      (html_tag): valid = common
class i       (html_tag): valid = common
class img     (single):
    valid    = ['alt', 'height', 'src', 'width', 'ismap', 'longdesc', 'usemap'] + common
    required = ['alt', 'src']
    default  = {'alt': ''}
class input   (single):   valid = ['alt', 'checked', 'maxlength', 'name', 'size', 'type', 'value', 'accept', 'accesskey', 'disabled', 'ismap', 'onblur', 'onchange', 'onfocus', 'onselect', 'readonly', 'src', 'tabindex', 'usemap'] + common
class kbd     (html_tag): valid = common
class label   (html_tag): valid = ['for', 'accesskey', 'onblur', 'onfocus'] + common
class _map    (html_tag): valid = common
class object  (html_tag): valid = ['classid', 'codebase', 'height', 'name', 'type', 'width', 'archive', 'codetype', 'data', 'declare', 'standby', 'tabindex', 'usemap'] + common
class q       (html_tag): valid = ['cite'] + common
class ruby    (html_tag): valid = common
class samp    (html_tag): valid = common
class select  (html_tag): valid = ['multiple', 'name', 'size', 'disabled', 'onblur', 'onchange', 'onfocus', 'tabindex'] + common
class small   (html_tag): valid = common
class span    (html_tag): valid = common
class strong  (html_tag): valid = common
class sub     (html_tag): valid = common
class sup     (html_tag): valid = common
class textarea(html_tag): valid = ['cols', 'name', 'rows', 'accesskey', 'disabled', 'onblur', 'onchange', 'onfocus', 'onselect', 'readonly', 'tabindex'] + common
class tt      (ugly):     valid = common
class var     (html_tag): valid = common

#List item elements
class dd(html_tag): valid = common
class dt(html_tag): valid = common
class li(html_tag): valid = common

#Table content elements
class caption (html_tag): valid = common
class col     (single):   valid = ['align', 'span', 'valign', 'width', 'char', 'charoff'] + common
class colgroup(html_tag): valid = ['align', 'span', 'valign', 'width', 'char', 'charoff'] + common
class tbody   (html_tag): valid = ['align', 'valign', 'char', 'charoff'] + common
class td      (html_tag): valid = ['align', 'colspan', 'headers', 'rowspan', 'valign', 'axis', 'char', 'charoff'] + common
class tfoot   (html_tag): valid = ['align', 'valign', 'char', 'charoff'] + common
class th      (html_tag): valid = ['abbr', 'align', 'colspan', 'rowspan', 'valign', 'axis', 'char', 'charoff', 'scope'] + common
class thead   (html_tag): valid = ['align', 'valign', 'char', 'charoff'] + common
class tr      (html_tag): valid = ['align', 'valign', 'char', 'charoff'] + common

#Form fieldset legends
class legend(html_tag): valid = ['accesskey'] + common

#Form menu options
class optgroup(html_tag): valid = ['label', 'disabled'] + common
class option  (html_tag): valid = ['selected', 'value', 'disabled', 'label'] + common

#Map areas
class area(single):
    valid    = ['alt', 'coords', 'href', 'shape', 'accesskey', 'onblur', 'onfocus', 'nohref', 'tabindex'] + common
    required = ['alt']
    default  = {'alt': ''}

#Object parameters
class param(single):
    valid    = ['name', 'value', 'id', 'type', 'valuetype']
    required = ['name']

#Ruby annotations
class rb (html_tag): valid = common
class rbc(html_tag): valid = common
class rp (html_tag): valid = common
class rt (html_tag): valid = ['rbspan'] + common
class rtc(html_tag): valid = common

################################################################################
################## Utilities for easily manipulating HTML ######################
################################################################################

class include(html_tag):
    def __init__(self, f):
        fl = file(f, 'rb')
        self.data = fl.read()
        fl.close()
        
    def render(self, n=1, do_inline=False):
        return self.data
        
def pread(cmd, data='', mode='t'):
    import os
    fin, fout = os.popen4(cmd, mode)
    fin.write(data)
    fin.close()
    return fout.read()
        
class pipe(html_tag):
    def __init__(self, cmd, data=''):
        self.data = pread(cmd, data)
        
    def render(self, n=1, do_inline=False):
        return self.data

class escape(html_tag):
    def render(self, n=1, do_inline=False):
        return self.escape(html_tag.render_children(self, n))
        
    def escape(self, s, quote=None): # stoled from std lib cgi 
        '''Replace special characters "&", "<" and ">" to HTML-safe sequences.
        If the optional flag quote is true, the quotation mark character (")
        is also translated.'''
        s = s.replace("&", "&amp;") # Must be done first!
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        if quote:
            s = s.replace('"', "&quot;")
        return s


_unescape = {'quot' :34,
             'amp'  :38,
             'lt'   :60,
             'gt'   :62,
             'nbsp' :32,
             
             # more here
             
             'yuml' :255
             }

def unescape(data):
    import re
    cc = re.compile('&(?:(?:#(\d+))|([^;]+));')
    
    result = []
    m = cc.search(data)
    while m:
        result.append(data[0:m.start()])
        d = m.group(1)
        if d:
            d = int(d)
            result.append(d > 255 and unichr(d) or chr(d))
        else:
            d = _unescape.get(m.group(2), ord('?'))
            result.append(d > 255 and unichr(d) or chr(d))
            
            
        data = data[m.end():]
        m = cc.search(data)
    
    result.append(data)
    return ''.join(result)
    
    
class lazy(html):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def render(self, n=1, do_inline=False):
        return self.func(*self.args, **self.kwargs)

















