#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;

namespace SimpleUnityCI
{
	public class Builder
	{
		// This function will be called from the build process
		public static void Build()
		{
			List<string> buildIndexScenes = new List<string>();
			foreach (EditorBuildSettingsScene scene in EditorBuildSettings.scenes)
			{
				if (scene.enabled)
				{
					buildIndexScenes.Add(scene.path);
				}
			}

			string[] arguments = Environment.GetCommandLineArgs();
			Dictionary<string, bool> flags = new Dictionary<string, bool>()
			{
				{ "-outputPath", false },
				{ "-buildTarget", false },
				{ "-keystoreName", false },
				{ "-keystorePass", false },
				{ "-keyaliasName", false },
				{ "-keyaliasPass", false },
			};
			Dictionary<string, string> values = new Dictionary<string, string>();
			foreach (string argument in arguments)
			{
				KeyValuePair<string, bool> searchingFor = flags.FirstOrDefault(kvp => kvp.Value);
				if (!string.IsNullOrEmpty(searchingFor.Key))
				{
					values[searchingFor.Key] = argument;
					flags[searchingFor.Key] = false;
				}

				if (flags.ContainsKey(argument))
				{
					flags[argument] = true;
				}
			}

			if (values.TryGetValue("-keystoreName", out string value)) PlayerSettings.Android.keystoreName = value;
			if (values.TryGetValue("-keystorePass", out string value1)) PlayerSettings.Android.keystorePass = value1;
			if (values.TryGetValue("-keyaliasName", out string value2)) PlayerSettings.Android.keyaliasName = value2;
			if (values.TryGetValue("-keyaliasPass", out string value3)) PlayerSettings.Android.keyaliasPass = value3;

			Enum.TryParse(values["-buildTarget"], out BuildTarget buildTarget);
			BuildPlayerOptions options = new BuildPlayerOptions
			{
				scenes = buildIndexScenes.ToArray(),
				target = buildTarget,
				locationPathName = values["-outputPath"],
			};

			BuildPipeline.BuildPlayer(options);
		}
	}
}
#endif