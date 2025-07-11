// ui/src/components/management/ResourceTable.tsx
import React from 'react';
import { Link } from 'react-router-dom'; // Import Link for viewLinkPrefix
import Button from '../forms/Button';

export interface Column<T> {
  header: string;
  accessor: keyof T | ((item: T) => React.ReactNode);
  className?: string;
}

export interface ResourceTableProps<T extends { id: string }> {
  data: T[];
  columns: Column<T>[];
  onEdit?: (item: T) => void;
  onDelete?: (item: T) => void;
  onView?: (item: T) => void; // ADDED: For a generic view action
  isLoading?: boolean;
  viewLinkPrefix?: string; 
}

const ResourceTable = <T extends { id: string }>({
  data,
  columns,
  onEdit,
  onDelete,
  onView, // ADDED
  isLoading = false,
  viewLinkPrefix
}: ResourceTableProps<T>) => {
  if (isLoading) {
    return <div className="text-center py-10">Loading data...</div>;
  }
  if (!data || data.length === 0) {
    return <div className="text-center py-10 text-gray-500">No data available.</div>;
  }

  return (
    <div className="overflow-x-auto shadow border-b border-gray-200 sm:rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col, index) => (
              <th
                key={index}
                scope="col"
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${col.className || ''}`}
              >
                {col.header}
              </th>
            ))}
            {(onEdit || onDelete || viewLinkPrefix || onView) && ( // MODIFIED: Added onView to condition
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((item) => (
            <tr key={item.id} className="hover:bg-gray-50">
              {columns.map((col, index) => (
                <td key={index} className={`px-6 py-4 whitespace-nowrap text-sm text-gray-700 ${col.className || ''}`}>
                  {typeof col.accessor === 'function'
                    ? col.accessor(item)
                    : String(item[col.accessor] ?? '')}
                </td>
              ))}
              {(onEdit || onDelete || viewLinkPrefix || onView) && ( // MODIFIED: Added onView to condition
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  {viewLinkPrefix && !onView && ( // Only show if onView is not provided
                    <Link to={`${viewLinkPrefix}/${item.id}`} className="text-indigo-600 hover:text-indigo-900">
                      View (Link)
                    </Link>
                  )}
                  {onView && ( // ADDED: Generic View Button
                    <Button variant="ghost" size="sm" onClick={() => onView(item)} className="text-blue-600 hover:text-blue-800">
                        Details
                    </Button>
                  )}
                  {onEdit && (
                    <Button variant="ghost" size="sm" onClick={() => onEdit(item)}>
                        Edit
                    </Button>
                  )}
                  {onDelete && (
                     <Button variant="ghost" size="sm" onClick={() => onDelete(item)} className="text-red-600 hover:text-red-800">
                        Delete
                    </Button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResourceTable;