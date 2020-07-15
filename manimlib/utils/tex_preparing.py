class TexFile:
	"""Represents a body of .tex template. Can change its
	parameters and gives you body for captions and formulas.

	List of parameters:
		sans_font: Set sans font of the document.
		roman_font, mono_font: The same.
		pre_packages: These packages will be included into preamble at its
			beginning. Is array.
		post_packages: Packages to place at the end of preamble. Is array.

	To change or unset these parameters use unset_prop() and set_prop() methods.
	If parameter is array, just use append_prop().

	"""

	def __init__(self, file_address):
		self.origin_body = open(file_address).read()
		self.templated_body = None
		self.state = {
			"sans_font": False,
			"roman_font": False,
			"mono_font": False,
			"pre_packages": [],
			"post_packages": []
		}
		self.is_formula = False

	def unset_prop(self, name: str):
		# I think no need to catch exception here
		self.state[name] = (
			[]
			if isinstance(self.state[name], list)
			else False
		)

	def set_prop(self, name: str, value):
		self.state[name] = value

	def append_prop(self, name: str, value):
		"""Use this method instead of set_prop if the parameter is an array.
		"""
		self.state[name].append(value)

	def reapply_templates(self):
		"""Remember body with applied parameters. This function can be called
		if they was changed.
		"""

		self.templated_body = str(self.origin_body)

		for label, value in self.state.items():

			if not value:
				continue

			replace_by = ""

			if label == "sans_font":
				replace_by = (
					"\\setsansfont[Mapping=tex-text]{%s}" % value
				)
			elif label == "roman_font":
				replace_by = (
					"\\setromanfont[Mapping=tex-text]{%s}" % value
				)
			elif label == "mono_font":
				replace_by = (
					"\\setmonofont[Mapping=tex-text]{%s}" % value
				)
			elif label in ["pre_packages", "post_packages"]:
				replace_by = "\n".join([
					"\\usepackage{%s}" % package
					for package in value
				])

			self.templated_body = self.templated_body.replace(
				"%%!template:%s" % label, replace_by
			)

	def get_body(self, caption: str) -> str:
		return self.templated_body.replace(
			"%!template:content", caption)

	def get_aligned_body(self, formula: str) -> str:
		print(self.templated_body.replace(
			"%!template:content",
			"\\begin{align*}\n%s\n\\end{align*}" % formula
		))
		return self.templated_body.replace(
			"%!template:content",
			"\\begin{align*}\n%s\n\\end{align*}" % formula
		)

	def configurate(self, config):
		"""Set self.state to configs given in `config`.
		"""
		for key in self.state.keys():
			if key in config:
				self.state[key] = config[key] or False
		self.reapply_templates()
