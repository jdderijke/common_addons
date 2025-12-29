from common_addons.common_utils import update_css_stylestr
orig_style = f'position:relative;height:100%;width:100%;background:transparent;overflow:auto;padding:10px'
new_style = f'white-space:nowrap;width:auto;height:auto;font-size:1.0em'

def main():
	print(update_css_stylestr(orig_style, new_style))
	
if __name__ == '__main__':
	main()

