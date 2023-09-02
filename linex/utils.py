import inspect
from typing import Any, Callable, Optional


def get_params_with_types(func: Callable) -> dict[
        str,
        Optional[
            list[
                tuple[str, Any]
            ]
        ]
    ]:
    """Gets the parameters with type annotations retrieving.

    Args:
        func (:obj:`Callable`): The function to retrieve.

    Raises:
        TypeError: Keyword-only arguments should only remain one in this case.
    """
    params = inspect.signature(func).parameters
    meta = {
        "regular": [],
        "kw": None
    }

    for index, param in enumerate(params):
        if index == 0:
            # ctx, ...
            continue

        this = params[param]
        ann = params[param].annotation

        if this.kind.name == "KEYWORD_ONLY":
            if meta['kw']:
                raise TypeError(
                    "Keyword-only arguments (followed by an asterisk *), "
                    "should only have one, but got more than one.\n"
                    f"- Current keyword-only arg: {meta['kw'][0]!r}\n"
                    f"- Error keyword-only arg: {param!r}"
                )

            meta['kw'] = (param, ann)
        else:
            meta['regular'].append((
                param,
                ann
            ))

    return meta

def postback_data(
    name: str,
    *data: Any
) -> str:
    """A helper function for creating Linex-compatible data (custom ID) strings.

    Everything will be string-ified.

    Args:
        name (str): The category / name. (Anything you want)
        *data (Any): Any data.
    """
    return f"{name};{';'.join((str(i) for i in data))}"
