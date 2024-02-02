using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json;
using UnityEditor;
using UnityEngine;
using UnityEngine.Networking;

namespace SimpleUnityCI
{
	[CreateAssetMenu(menuName = "Scriptable Assets/CI Build Settings")]
	public class CIBuildSettings : ScriptableObject
	{
		public string buildServer = "https://";
		public string gitRepo = "git@github.com:org/proj.git";
		public string branch = "";

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
				{ "branch", branch },
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


#if UNITY_EDITOR
	[CustomEditor(typeof(CIBuildSettings))]
	public class TestScriptableEditor : Editor
	{
		public override void OnInspectorGUI()
		{
			base.OnInspectorGUI();
			CIBuildSettings script = (CIBuildSettings)target;
			
			GUILayout.Space(10);

			if (GUILayout.Button("Build Window"))
			{
				// EditorWindow.GetWindow(System.Type.GetType("SimpleUnityCI.CIWindow,UnityEditor"));
				EditorApplication.ExecuteMenuItem("Window/Simple Unity CI");
			}

			if (GUILayout.Button("Build Remotely", GUILayout.Height(40)))
			{
				// make a request to the build server with the buildsettings as the post body
				script.buildServer = script.buildServer.TrimEnd('/');
				string url = script.buildServer + "/build";
				Debug.Log(url);
				Debug.Log(JsonConvert.SerializeObject(script.ToDict()));
				UnityWebRequest www = UnityWebRequest.Post(url, JsonConvert.SerializeObject(script.ToDict()), "application/json");
				www.SendWebRequest();
			}

			if (GUILayout.Button("Build Locally", GUILayout.Height(40)))
			{
				if (script.androidKeystoreSettings.keystoreName != "") PlayerSettings.Android.keystoreName = script.androidKeystoreSettings.keystoreName;
				if (script.androidKeystoreSettings.keystorePass != "") PlayerSettings.Android.keystorePass = script.androidKeystoreSettings.keystorePass;
				if (script.androidKeystoreSettings.keyaliasName != "") PlayerSettings.Android.keyaliasName = script.androidKeystoreSettings.keyaliasName;
				if (script.androidKeystoreSettings.keyaliasPass != "") PlayerSettings.Android.keyaliasPass = script.androidKeystoreSettings.keyaliasPass;
				BuildPlayerOptions options = new BuildPlayerOptions
				{
					scenes = (from scene in EditorBuildSettings.scenes where scene.enabled select scene.path).ToArray(),
					target = EditorUserBuildSettings.activeBuildTarget,
					locationPathName = EditorUserBuildSettings.activeBuildTarget == BuildTarget.Android ? $"Builds/SUCI/{Application.productName}.apk" : $"Builds/SUCI/Build",
				};

				BuildPipeline.BuildPlayer(options);
			}
		}
	}
#endif
}