using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;
using System.Reflection;

[assembly: AssemblyTitle("LipidDrop Imaging")]
[assembly: AssemblyDescription("Adipocyte-guided Raman imaging launcher")]
[assembly: AssemblyProduct("LipidDrop Imaging")]
[assembly: AssemblyCompany("Avantika Negi / Koseki Lab")]
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: AssemblyFileVersion("1.0.0.0")]

internal static class Program
{
    private const string AppId = "avantikan7.LipidDropImaging.Adipocyte";
    private const string MutexName = "Local\\avantikan7.LipidDropImaging.Adipocyte";

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    private static extern int SetCurrentProcessExplicitAppUserModelID(string appId);

    [STAThread]
    private static int Main()
    {
        SetCurrentProcessExplicitAppUserModelID(AppId);

        bool createdNew;
        using (var mutex = new Mutex(true, MutexName, out createdNew))
        {
            if (!createdNew)
            {
                MessageBox.Show(
                    "LipidDrop Imaging is already running.",
                    "LipidDrop Imaging",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );
                return 0;
            }

            string workspace = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(
                Path.DirectorySeparatorChar,
                Path.AltDirectorySeparatorChar
            );
            string pythonw = @"C:\Users\spraman\anaconda3\envs\confocal_control_gui_cellpose4\pythonw.exe";
            string script = Path.Combine(workspace, "napari-raman-widget", "run_napari.py");

            if (!File.Exists(pythonw) || !File.Exists(script))
            {
                MessageBox.Show(
                    "The LipidDrop Python environment or launcher script could not be found.\n\n" +
                    "Python: " + pythonw + "\n" +
                    "Script: " + script,
                    "LipidDrop Imaging",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                return 1;
            }

            var startInfo = new ProcessStartInfo
            {
                FileName = pythonw,
                Arguments = "\"" + script + "\"",
                WorkingDirectory = workspace,
                UseShellExecute = false,
                CreateNoWindow = true,
            };

            try
            {
                using (Process process = Process.Start(startInfo))
                {
                    if (process == null)
                    {
                        throw new InvalidOperationException("Python process did not start.");
                    }
                    process.WaitForExit();
                    return process.ExitCode;
                }
            }
            catch (Exception error)
            {
                MessageBox.Show(
                    "LipidDrop Imaging could not start.\n\n" + error.Message,
                    "LipidDrop Imaging",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                return 1;
            }
        }
    }
}
