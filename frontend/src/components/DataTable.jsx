import React from 'react';
import './DataTable.css';

const DataTable = ({ data, columns, title, onRowClick }) => {
  if (!data || data.length === 0) {
    return (
      <div className="data-table-container">
        <h2>{title}</h2>
        <p>Нет данных для отображения</p>
      </div>
    );
  }

  return (
    <div className="data-table-container">
      <h2>{title}</h2>
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((column, index) => (
                <th key={index}>{column.header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => (
              <tr 
                key={index}
                onClick={() => onRowClick && onRowClick(item)}
                className={onRowClick ? 'clickable-row' : ''}
              >
                {columns.map((column, colIndex) => (
                  <td key={colIndex}>
                    {column.render ? column.render(item[column.key], item) : item[column.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataTable;