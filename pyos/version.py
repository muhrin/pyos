author_info = (('Martin Uhrin', 'martin.uhrin.10@ucl.ac.uk'),)
version_info = (0, 7, 13)

__author__ = ", ".join("{} <{}>".format(*info) for info in author_info)
__version__ = ".".join(map(str, version_info))

__all__ = ('__version__',)


def _strip_first_and_last_lines(text: str) -> str:
    return "\n".join(text.split("\n")[1:-1])


LOGO = _strip_first_and_last_lines(r"""
                  ____  ____ 
                 / __ \/ __ /
    ____  __  __/ / / / /_   
   / __ \/ / / / / / /\__ \  
  / /_/ / /_/ / /_/ /___/ /  
 / .___/\__, /\____//____/   
/_/    /____/                
""")

BANNER = _strip_first_and_last_lines(r"""
                  ____  ____ 
                 / __ \/ __ /
    ____  __  __/ / / / /_   
   / __ \/ / / / / / /\__ \  
  / /_/ / /_/ / /_/ /___/ /  
 / .___/\__, /\____//____/   
/_/    /____/                 v{}                 
""".format(__version__))
