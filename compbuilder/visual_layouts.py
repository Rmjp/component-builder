class NandLayoutMixin:
    LAYOUT_CONFIG = {
        'width' : 48,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 16,
        #'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     h 20
                     a 20,20,180,1,1,0,40
                     h -20
                     z" />
            <circle cx="44" cy="20" r="4"/>
        """,
    }


class NotLayoutMixin:
    LAYOUT_CONFIG = {
        'width' : 38,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 0,
        'label' : '',
        'ports' : {  # hide all port labels
            'In' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     l 30,20
                     l -30,20
                     z" />
            <circle cx="34" cy="20" r="4"/>
        """,
    }


class BufferLayoutMixin:
    LAYOUT_CONFIG = {
        'width' : 30,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 0,
        'label' : '',
        'ports' : {  # hide all port labels
            'In' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     l 30,20
                     l -30,20
                     z" />
        """,
    }


class AndLayoutMixin:
    LAYOUT_CONFIG = {
        'width' : 40,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 16,
        'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     h 20
                     a 20,20,180,1,1,0,40
                     h -20
                     z" />
        """,
    }


class OrLayoutMixin:
    LAYOUT_CONFIG = {
        'width' : 40,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 16,
        'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     h 5
                     q 25,0,35,20
                     q -10,20,-35,20
                     h -5
                     Q 10,20,0,0
                     z
                     M 0,10.5 h 4
                     M 0,29.5 h 4
                     " />
        """,
    }


class XorLayoutMixin:
    LAYOUT_CONFIG = {
        'width' : 45,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 16,
        'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 5,0
                     h 5
                     q 25,0,35,20
                     q -10,20,-35,20
                     h -5
                     q 10,-20,0,-40
                     z
                     M 0,40" />
            <path d="M 0,0
                     q 10,20,0,40
                     M 0,10.5 h 4
                     M 0,29.5 h 4" style="fill:none"/>
        """,
    }
