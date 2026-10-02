# Build Cycles shader math from a Python expression, so a procedural field reads like the numpy code that drives the
# stars: compile(nt, "exp(-r / 24) * arms", env) → an output socket. It never imports bpy: it adds nodes to the node tree its caller (galaxy.py) passes in.
#
# Supported: numbers, + - * / ** and unary -, names (env: name → socket or number), and the calls
#   sin cos tan exp log sqrt abs floor fract min max atan2 pow mod clamp(x, a, b) smooth(e0, e1, x) mix(a, b, u)
#   noise(x, y, z, scale, [detail, rough, w]) → Noise Texture (4D when w is given), its Fac
# A name that is not in env is an error (no silent zeros). Shared sub-expressions: bind them in env first.
import ast

MATH = {"sin": "SINE", "cos": "COSINE", "tan": "TANGENT", "exp": "EXPONENT", "sqrt": "SQRT", "abs": "ABSOLUTE",
        "floor": "FLOOR", "fract": "FRACT", "min": "MINIMUM", "max": "MAXIMUM", "atan2": "ARCTAN2", "pow": "POWER",
        "mod": "FLOORED_MODULO"}
BIN = {ast.Add: "ADD", ast.Sub: "SUBTRACT", ast.Mult: "MULTIPLY", ast.Div: "DIVIDE", ast.Pow: "POWER"}


class Compiler:
    def __init__(self, nt):
        self.nt = nt; self.x = 0

    def node(self, kind):
        n = self.nt.nodes.new(kind); n.location = (self.x, 0); self.x += 30
        return n

    def math(self, op, a, b=None, c=None):
        n = self.node("ShaderNodeMath"); n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = float(v)
            else: self.nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    def put(self, sock_in, v):
        if isinstance(v, (int, float)): sock_in.default_value = float(v)
        else: self.nt.links.new(v, sock_in)

    def ev(self, e, env):
        if isinstance(e, ast.Constant): return float(e.value)
        if isinstance(e, ast.Name):
            if e.id not in env: raise NameError(f"nodexpr: unknown name {e.id!r}")
            return env[e.id]
        if isinstance(e, ast.UnaryOp) and isinstance(e.op, ast.USub):
            v = self.ev(e.operand, env)
            return -v if isinstance(v, float) else self.math("MULTIPLY", v, -1.0)
        if isinstance(e, ast.BinOp) and type(e.op) in BIN:
            a, b = self.ev(e.left, env), self.ev(e.right, env)
            if isinstance(a, float) and isinstance(b, float):
                return {ast.Add: a + b, ast.Sub: a - b, ast.Mult: a * b, ast.Div: a / b, ast.Pow: a ** b}[type(e.op)]
            return self.math(BIN[type(e.op)], a, b)
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Name):
            f = e.func.id; args = [self.ev(a, env) for a in e.args]
            if f == "log": return self.math("LOGARITHM", args[0], 2.718281828459045)
            if f in MATH: return self.math(MATH[f], *args)
            if f == "clamp": return self.math("MINIMUM", self.math("MAXIMUM", args[0], args[1]), args[2])
            if f == "mix":
                a, b, u = args; return self.math("ADD", a, self.math("MULTIPLY", self.math("SUBTRACT", b, a), u))
            if f == "smooth":                                           # smoothstep(e0, e1, x)
                e0, e1, x = args; n = self.node("ShaderNodeMapRange"); n.interpolation_type = "SMOOTHSTEP"; n.clamp = True
                self.put(n.inputs["Value"], x); self.put(n.inputs["From Min"], e0); self.put(n.inputs["From Max"], e1)
                n.inputs["To Min"].default_value = 0.0; n.inputs["To Max"].default_value = 1.0
                return n.outputs["Result"]
            if f == "noise":
                x, y, z, scale = args[:4]; detail = args[4] if len(args) > 4 else 4.0; rough = args[5] if len(args) > 5 else 0.55
                n = self.node("ShaderNodeTexNoise"); n.noise_dimensions = "4D" if len(args) > 6 else "3D"
                cx = self.node("ShaderNodeCombineXYZ")
                for i, v in enumerate((x, y, z)): self.put(cx.inputs[i], v)
                self.nt.links.new(cx.outputs[0], n.inputs["Vector"])
                self.put(n.inputs["Scale"], scale); self.put(n.inputs["Detail"], detail); self.put(n.inputs["Roughness"], rough)
                if len(args) > 6: self.put(n.inputs["W"], args[6])
                return n.outputs["Fac"]
            raise NameError(f"nodexpr: unknown function {f!r}")
        raise SyntaxError(f"nodexpr: unsupported {ast.dump(e)[:80]}")


def compile_expr(nt, src, env, comp=None):
    comp = comp or Compiler(nt)
    v = comp.ev(ast.parse(src, mode="eval").body, env)
    if isinstance(v, float):                                           # a constant: still hand back a socket
        n = comp.node("ShaderNodeValue"); n.outputs[0].default_value = v; return n.outputs[0]
    return v


def bind(nt, env, defs, comp=None):
    """defs: [(name, expr), …] compiled in order; each becomes a name the later ones can use"""
    comp = comp or Compiler(nt)
    for name, src in defs: env[name] = compile_expr(nt, src, env, comp)
    return env
