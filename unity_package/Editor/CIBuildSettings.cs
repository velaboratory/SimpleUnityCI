using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace SimpleUnityCI
{
	[CreateAssetMenu(menuName = "Scriptable Assets/CI Build Settings")]
	public class CIBuildSettings : ScriptableObject
	{
		public string buildServer = "https://";
		public string gitRepo = "git@github.com:org/proj.git";

		public enum BuildTargets
		{
			StandaloneWindows64,
			Android
		}

		public BuildTargets buildTarget = BuildTargets.Android;

		[System.Serializable]
		public class AndroidKeystoreSettings
		{
			public string keystoreName = "";
			public string keystorePass = "";
			public string keyaliasName = "";
			public string keyaliasPass = "";
		}

		public AndroidKeystoreSettings androidKeystoreSettings;

		[System.Serializable]
		public class OculusUploadSettings
		{
			public string oculusAppId = "";
			public string oculusAppSecret = "";
			public string oculusReleaseChannel = "DEV";
		}

		public OculusUploadSettings oculusUploadSettings;

		public Dictionary<string, string> ToDict()
		{
			return new Dictionary<string, string>
			{
				{ "git_repo", gitRepo },
				{ "build_target", buildTarget.ToString() },
				{ "oculus_app_id", oculusUploadSettings.oculusAppId },
				{ "oculus_app_secret", oculusUploadSettings.oculusAppSecret },
				{ "oculus_release_channel", oculusUploadSettings.oculusReleaseChannel },
				{ "keystore_name", androidKeystoreSettings.keystoreName },
				{ "keystore_pass", androidKeystoreSettings.keystorePass },
				{ "keyalias_name", androidKeystoreSettings.keyaliasName },
				{ "keyalias_pass", androidKeystoreSettings.keyaliasPass },
			};
		}
	}


	[CustomEditor(typeof(CIBuildSettings))]
	public class TestScriptableEditor : Editor
	{
		public override void OnInspectorGUI()
		{
			base.OnInspectorGUI();
			CIBuildSettings script = (CIBuildSettings)target;

			if (GUILayout.Button("Build Window", GUILayout.Height(40)))
			{
				// EditorWindow.GetWindow(System.Type.GetType("SimpleUnityCI.CIWindow,UnityEditor"));
				EditorApplication.ExecuteMenuItem("Window/Simple Unity CI");
			}
		}
	}
}