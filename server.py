#! /usr/bin/env python
# encoding: utf-8

from flask import Flask, render_template, url_for, request
import json, os, random, urllib2, uuid, socket, sys

app = Flask(__name__)
app.registered = False
app.current_op = None
allowed_ops = '+-*/'
HUB = 'http://localhost:8000'

def send_registration():
  registration = dict(id=str(uuid.uuid4()), 
      host=socket.gethostname(), 
      active=True, 
      operator=app.current_op, 
      calculation='/evaluate'
  )
  request = urllib2.Request(HUB, json.dumps(registration), {'Content-Type': 'application/json'})
  try:
    urllib2.urlopen(request)
  except urllib2.URLError:
    pass

def register_me():
  try:
    app.current_op = os.environ['OP']
  except KeyError:
    app.current_op = random.sample(allowed_ops, 1)[0]
  print "Current op: %s" % app.current_op
  send_registration()
  app.registered = True

def find_calculators():
  # TODO: pobierz to z huba
  make_host = lambda op,port: dict(host="127.0.0.1:%s" % port, active=True, calculation='/evaluate', operator=op)
  app.calculators = {
      '+': [make_host('+', 5001)],
      '-': [make_host('-', 5002)],
      '*': [make_host('*', 5003)],
      '/': [make_host('/', 5004)]
  }

def execute_op(operator, arg1, arg2):
  calculator = random.sample(app.calculators[operator], 1)[0]
  params = json.dumps(dict(number1=arg1, number2=arg2))
  url = "http://%s%s" % (calculator['host'], calculator['calculation'])
  print url
  request = urllib2.Request(url, params, {'Content-Type': 'application/json'})
  fp = urllib2.urlopen(request)
  data = fp.read()
  print data
  return int(data)

@app.route('/evaluate', methods=['POST'])
def evaluate():
  data = json.loads(request.data)
  print "%r" % data
  arg1 = int(data['number1'])
  arg2 = int(data['number2'])
  if app.current_op == '+':
    result = arg1 + arg2
  elif app.current_op == '-':
    result = arg2 - arg1 # NOTE: kolejność odwrotna, wychodzi poprawnie ale tricky
  elif app.current_op == '*':
    result = arg1 * arg2
  elif app.current_op == '/':
    result = arg2 / arg1 # NOTE: jw
  return str(result)

@app.route('/', methods=['POST'])
def send():
  expr = request.form['onp']
  stack = []
  tokens = expr.split()
  while tokens: # zakładamy że wyrażenie poprawne
    print "stack %r tokens %r" % (stack, tokens)
    arg = tokens.pop(0)
    if arg.isdigit() or (arg[0] == '-' and arg[1:].isdigit()): # wszystkie znaki cyframi, ewentualnie minus
      stack.append(arg)
    elif arg in allowed_ops:
      result = execute_op(arg, stack.pop(), stack.pop())
      stack.append(result)
    print "stack %r tokens %r" % (stack, tokens)
  return render_template('index.html', result=stack.pop())
  
@app.route('/', methods=['GET'])
def index():
  return render_template('index.html', result=None)

if __name__ == "__main__":
  register_me()
  find_calculators()
  app.debug = os.environ.has_key('DEBUG')
  if len(sys.argv) >= 2:
    app.run(port=int(sys.argv[1]))
  else:
    app.run()
