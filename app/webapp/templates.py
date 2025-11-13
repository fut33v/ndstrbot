"""HTML templates for displaying database content."""

def generate_table_html(title: str, headers: list, rows: list) -> str:
    """Generate HTML table for displaying data."""
    # Generate table headers
    header_html = ""
    for header in headers:
        header_html += f"<th>{header}</th>"
    
    # Generate table rows
    rows_html = ""
    for row in rows:
        row_html = "<tr>"
        for cell in row:
            row_html += f"<td>{cell}</td>"
        row_html += "</tr>"
        rows_html += row_html
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                text-align: center;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .back-link {{
                display: inline-block;
                margin-bottom: 20px;
                padding: 10px 15px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }}
            .back-link:hover {{
                background-color: #0056b3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/dashboard" class="back-link">← Back to Dashboard</a>
            <h1>{title}</h1>
            <table>
                <thead>
                    <tr>
                        {header_html}
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html

def format_datetime(dt):
    """Format datetime for display."""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return ""