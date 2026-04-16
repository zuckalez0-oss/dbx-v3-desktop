# motor de geração e leitura de arquivos DXF

import re
import math
import io
import ezdxf
from ezdxf import bbox


def _safe_filename_token(value, fallback):
    token = str(value).strip() if value is not None else ""
    if not token:
        token = fallback
    return re.sub(r'[^\w.-]+', '_', token)


def _format_thickness(value):
    if value is None or value == "":
        return "SemEspessura"
    try:
        numeric_value = float(str(value).replace(',', '.'))
        return f"{numeric_value:.2f}"
    except (TypeError, ValueError):
        return str(value).strip()

#func criação do desenho dxf
def create_dxf_drawing(params: dict):
    """Gera um desenho DXF a partir de um dicionário de parâmetros já preparado."""
    try:
        doc = ezdxf.new('R2000')
        msp = doc.modelspace()
        
        doc.layers.new('CONTORNO', dxfattribs={'color': 1}) # Vermelho
        if params.get('holes'):
            doc.layers.new('FUROS', dxfattribs={'color': 3}) # Verde

        shape_type = params.get('shape')
        

        shape_creators = {
            'rectangle': lambda m, p: m.add_lwpolyline([(0,0),(p.get('width', 0),0),(p.get('width', 0),p.get('height', 0)),(0,p.get('height', 0))], close=True),
            'circle': lambda m, p: m.add_circle(center=(p.get('diameter', 0)/2, p.get('diameter', 0)/2), radius=p.get('diameter', 0)/2),
            'right_triangle': lambda m, p: m.add_lwpolyline([(0,0),(p.get('rt_base', 0),0),(0,p.get('rt_height', 0))], close=True),
            'trapezoid': lambda m, p: m.add_lwpolyline([
                (0,0), (p.get('trapezoid_large_base',0),0),
                (p.get('trapezoid_large_base',0)-((p.get('trapezoid_large_base',0)-p.get('trapezoid_small_base',0))/2),p.get('trapezoid_height',0)),
                (((p.get('trapezoid_large_base',0)-p.get('trapezoid_small_base',0))/2),p.get('trapezoid_height',0))
            ], close=True)
        }
        
        if shape_type in shape_creators:
            shape_creators[shape_type](msp, params).dxf.layer = 'CONTORNO'
        else:
            return None, f"Forma '{shape_type}' desconhecida."

        for hole in params.get('holes', []):
            msp.add_circle(center=(hole['x'], hole['y']), radius=hole['diameter']/2, dxfattribs={'layer': 'FUROS'})

        stream = io.StringIO()
        doc.write(stream)
        project_number = params.get('project_number') or params.get('numero_projeto') or params.get('projeto') or params.get('Projeto')
        part_name = params.get('part_name')
        thickness_label = _format_thickness(params.get('thickness'))

        filename = "{}_{}_{}MM".format(
            _safe_filename_token(project_number, "SemProjeto"),
            _safe_filename_token(part_name, "SemNome"),
            _safe_filename_token(thickness_label, "SemEspessura")
        )
        return stream.getvalue(), f"{filename}.dxf"

    except Exception as e:
        print(f"Erro inesperado no desenho do DXF: {e}")
        return None, "Erro interno de desenho."

def prepare_and_validate_dxf_data(raw_data: dict): 
    """Prepara e valida os dados para a geração do DXF (sem cotas ou texto)."""
    params = raw_data.copy()


    params['part_name'] = params.get('nome_arquivo')
    params['project_number'] = params.get('project_number') or params.get('numero_projeto') or params.get('projeto') or params.get('Projeto')
    params['thickness'] = params.get('espessura')
    params['shape'] = params.get('forma')
    params['width'] = params.get('largura')
    params['height'] = params.get('altura')
    params['diameter'] = params.get('diametro')

    params['include_dims'] = False 
    params['include_text_info'] = False
    
    if not params.get('part_name') or not params.get('shape'):
        return None, "Dados insuficientes: 'part_name' ou 'shape' ausentes."

    def to_float(value, default=0.0):
        if value is None or value == '': return default
        try: return float(str(value).replace(',', '.'))
        except (ValueError, TypeError): return default

    numeric_keys = [
        'width', 'height', 'diameter', 'rt_base', 'rt_height', 
        'trapezoid_large_base', 'trapezoid_small_base', 'trapezoid_height'
    ]
    for key in numeric_keys:
        params[key] = to_float(params.get(key))
        

    params['holes'] = []
    if 'furos' in params and isinstance(params['furos'], list):
        for furo_pyqt in params['furos']:
            params['holes'].append({
                'diameter': to_float(furo_pyqt.get('diam')),
                'x': to_float(furo_pyqt.get('x')),
                'y': to_float(furo_pyqt.get('y'))
            })
            
    return params, None


def get_dxf_bounding_box(file_path: str):
    """
    Lê um arquivo DXF e calcula o bounding box (largura e altura) de seu conteúdo.

    :param file_path: Caminho para o arquivo DXF.
    :return: Uma tupla (largura, altura) ou (None, None) em caso de erro.
    """
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()

        cache = bbox.Cache()
        overall_bbox = bbox.extents(msp, cache=cache)

        if not overall_bbox.has_data:
            return None, None 

        return overall_bbox.size.x, overall_bbox.size.y
    except (IOError, ezdxf.DXFStructureError) as e:
        print(f"Erro ao ler ou processar o DXF '{file_path}': {e}")
        return None, None