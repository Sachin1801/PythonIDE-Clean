/**
 * Reusable File Upload Composable
 * Handles both single file uploads and bulk uploads to multiple students
 * Supports folder structures with preservation of relative paths
 */

import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';

export function useFileUpload() {
  const uploading = ref(false);
  const selectedFiles = ref([]);
  const fileStructure = ref([]);
  const uploadError = ref('');
  const uploadMode = ref('files'); // 'files' or 'folder'
  const supportedExtensions = ['.py', '.txt', '.csv', '.pdf'];

  /**
   * Process individual files for upload
   * @param {File[]} files - Array of File objects
   */
  const processFiles = (files) => {
    uploadError.value = '';
    const validFiles = [];
    const invalidFiles = [];

    files.forEach(file => {
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

      if (supportedExtensions.includes(fileExtension)) {
        if (file.size <= 10 * 1024 * 1024) { // 10MB limit
          validFiles.push(file);
        } else {
          invalidFiles.push(`${file.name} (too large, max 10MB)`);
        }
      } else {
        invalidFiles.push(`${file.name} (unsupported format)`);
      }
    });

    if (invalidFiles.length > 0) {
      uploadError.value = `Invalid files: ${invalidFiles.join(', ')}`;
    }

    // Add valid files (avoid duplicates)
    validFiles.forEach(file => {
      const exists = selectedFiles.value.some(existing =>
        existing.name === file.name && existing.size === file.size
      );
      if (!exists) {
        selectedFiles.value.push(file);
      }
    });

    return { validFiles, invalidFiles };
  };

  /**
   * Process folder files with preserved structure
   * @param {File[]} files - Array of File objects with webkitRelativePath
   */
  const processFolderFiles = (files) => {
    uploadError.value = '';
    const validFiles = [];
    const invalidFiles = [];
    fileStructure.value = [];

    files.forEach(file => {
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
      const relativePath = file.webkitRelativePath || file.relativePath || file.name;

      if (supportedExtensions.includes(fileExtension)) {
        if (file.size <= 10 * 1024 * 1024) {
          validFiles.push(file);
          fileStructure.value.push({
            file: file,
            relativePath: relativePath,
            name: file.name,
            size: file.size
          });
        } else {
          invalidFiles.push(`${relativePath} (too large, max 10MB)`);
        }
      }
    });

    if (invalidFiles.length > 0) {
      uploadError.value = `Invalid files: ${invalidFiles.join(', ')}`;
    }

    selectedFiles.value = validFiles;

    if (selectedFiles.value.length === 0 && files.length > 0) {
      uploadError.value = 'No supported files found in the selected folder';
    }

    return { validFiles, invalidFiles };
  };

  /**
   * Upload files to a single destination
   * @param {Object} options - Upload options
   * @param {string} options.projectName - Target project name (e.g., "Local/sa9082")
   * @param {string} options.parentPath - Parent path within project
   * @param {string} options.sessionId - User session ID
   * @param {Function} options.onProgress - Progress callback
   */
  const uploadFiles = async ({ projectName, parentPath, sessionId, onProgress }) => {
    if (selectedFiles.value.length === 0) {
      throw new Error('No files selected');
    }

    uploading.value = true;

    try {
      const uploadPromises = selectedFiles.value.map(async (file, index) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('projectName', projectName);
        formData.append('parentPath', parentPath);
        formData.append('filename', file.name);

        // Add relative path for folder uploads
        if (uploadMode.value === 'folder' && fileStructure.value[index]) {
          const relativePath = fileStructure.value[index].relativePath;
          formData.append('relativePath', relativePath);
          formData.append('preserveStructure', 'true');
        }

        const response = await fetch('/api/upload-file', {
          method: 'POST',
          body: formData,
          headers: {
            'session-id': sessionId
          }
        });

        const result = await response.json();
        if (!result.success) {
          throw new Error(`Failed to upload ${file.name}: ${result.error}`);
        }

        if (onProgress) {
          onProgress(index + 1, selectedFiles.value.length);
        }

        return result;
      });

      const results = await Promise.all(uploadPromises);
      return { success: true, results, count: results.length };

    } catch (error) {
      console.error('[useFileUpload] Error uploading files:', error);
      throw error;
    } finally {
      uploading.value = false;
    }
  };

  /**
   * Bulk upload files to multiple students
   * @param {Object} options - Bulk upload options
   * @param {string|string[]} options.targetStudents - "all" or array of usernames
   * @param {string} options.commonFolder - Common folder name (e.g., "Examples")
   * @param {string} options.subPath - Optional subdirectory path
   * @param {string} options.sessionId - User session ID
   * @param {Function} options.onProgress - Progress callback
   */
  const bulkUploadFiles = async ({ targetStudents, commonFolder, subPath, sessionId, onProgress }) => {
    if (selectedFiles.value.length === 0) {
      throw new Error('No files selected');
    }

    uploading.value = true;

    try {
      const targetStudentsParam = Array.isArray(targetStudents)
        ? JSON.stringify(targetStudents)
        : targetStudents;

      const uploadPromises = selectedFiles.value.map(async (file, index) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('targetStudents', targetStudentsParam);
        formData.append('commonFolder', commonFolder);
        formData.append('subPath', subPath || '');
        formData.append('filename', file.name);

        // Add relative path for folder uploads
        if (uploadMode.value === 'folder' && fileStructure.value[index]) {
          const relativePath = fileStructure.value[index].relativePath;
          formData.append('relativePath', relativePath);
          formData.append('preserveStructure', 'true');
        }

        const response = await fetch('/api/bulk-upload', {
          method: 'POST',
          body: formData,
          headers: {
            'session-id': sessionId
          }
        });

        const result = await response.json();
        if (!result.success) {
          throw new Error(`Failed to upload ${file.name}: ${result.error}`);
        }

        if (onProgress) {
          onProgress(index + 1, selectedFiles.value.length);
        }

        return result;
      });

      const results = await Promise.all(uploadPromises);

      // Calculate statistics
      const totalUploaded = results.reduce((sum, r) => sum + r.uploaded_to, 0);
      const failedStudents = results.reduce((acc, r) => {
        if (r.failed_students && r.failed_students.length > 0) {
          return acc.concat(r.failed_students);
        }
        return acc;
      }, []);

      return {
        success: true,
        results,
        totalFiles: results.length,
        totalUploaded,
        failedStudents: [...new Set(failedStudents)] // Remove duplicates
      };

    } catch (error) {
      console.error('[useFileUpload] Error in bulk upload:', error);
      throw error;
    } finally {
      uploading.value = false;
    }
  };

  /**
   * Traverse file tree for drag-and-drop folder uploads
   * @param {FileSystemEntry} item - File system entry from drag-and-drop
   * @param {File[]} filesList - Array to populate with files
   * @param {string} path - Current path
   */
  const traverseFileTree = async (item, filesList, path = '') => {
    if (item.isFile) {
      return new Promise((resolve) => {
        item.file((file) => {
          file.relativePath = path + file.name;
          filesList.push(file);
          resolve();
        });
      });
    } else if (item.isDirectory) {
      const dirReader = item.createReader();
      return new Promise((resolve) => {
        dirReader.readEntries(async (entries) => {
          for (const entry of entries) {
            await traverseFileTree(entry, filesList, path + item.name + '/');
          }
          resolve();
        });
      });
    }
  };

  /**
   * Format file size for display
   * @param {number} bytes - File size in bytes
   */
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  /**
   * Reset upload state
   */
  const reset = () => {
    selectedFiles.value = [];
    fileStructure.value = [];
    uploadError.value = '';
    uploading.value = false;
  };

  return {
    // State
    uploading,
    selectedFiles,
    fileStructure,
    uploadError,
    uploadMode,
    supportedExtensions,

    // Methods
    processFiles,
    processFolderFiles,
    uploadFiles,
    bulkUploadFiles,
    traverseFileTree,
    formatFileSize,
    reset
  };
}
