import pandas as pd
import io

def generate_excel(df):
    """
    Génère un fichier Excel en mémoire à partir d'un DataFrame.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Planning')
        
        # Ajustement automatique de la largeur des colonnes
        worksheet = writer.sheets['Planning']
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_len
            
    return output.getvalue()
