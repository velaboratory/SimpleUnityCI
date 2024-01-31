#if UNITY_EDITOR
using Newtonsoft.Json;
using UnityEditor;
using UnityEditor.UIElements;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UIElements;

namespace SimpleUnityCI
{
	public class CIWindow : EditorWindow
	{
		[SerializeField] private VisualTreeAsset m_VisualTreeAsset = default;
		private Button createBuildSettingsButton;
		private Button openBuildSettingsButton;
		private ObjectField buildSettingsField;
		private Button buildButton;

		[MenuItem("Window/Simple Unity CI")]
		public static void ShowExample()
		{
			CIWindow wnd = GetWindow<CIWindow>();
			wnd.titleContent = new GUIContent("Simple Unity CI");
		}

		public void CreateGUI()
		{
			// Each editor window contains a root VisualElement object
			VisualElement root = rootVisualElement;

			// Instantiate UXML
			VisualElement labelFromUxml = m_VisualTreeAsset.Instantiate();
			root.Add(labelFromUxml);


			buildButton = labelFromUxml.Q<Button>(className: "build-button");
			createBuildSettingsButton = labelFromUxml.Q<Button>(className: "create-build-settings-button");
			buildSettingsField = labelFromUxml.Q<ObjectField>();
			Button findBuildSettings = labelFromUxml.Q<Button>(className: "find-build-settings");
			findBuildSettings.clicked += RefreshBuildSettingsExists;
			buildButton.clicked += Build;
			// openBuildSettingsButton.clicked += OpenBuildSettings;
			createBuildSettingsButton.clicked += CreateBuildSettings;

			RefreshBuildSettingsExists();
		}

		private void RefreshBuildSettingsExists()
		{
			if (FindBuildSettings())
			{
				createBuildSettingsButton.style.display = DisplayStyle.None;
				buildButton.style.display = DisplayStyle.Flex;
			}
			else
			{
				createBuildSettingsButton.style.display = DisplayStyle.Flex;
				buildButton.style.display = DisplayStyle.None;
			}
		}

		private bool FindBuildSettings()
		{
			string[] settings = AssetDatabase.FindAssets("t:CIBuildSettings");
			if (settings.Length > 0)
			{
				CIBuildSettings ciBuildSettings = AssetDatabase.LoadAssetAtPath<CIBuildSettings>(AssetDatabase.GUIDToAssetPath(settings[0]));
				Selection.activeObject = ciBuildSettings;
				if (ciBuildSettings == null)
				{
					Debug.Log("No build settings");
				}
				else
				{
					if (buildSettingsField == null)
					{
						Debug.Log("No build settings field");
					}
					else
					{
						buildSettingsField.SetValueWithoutNotify(ciBuildSettings);
						buildSettingsField.MarkDirtyRepaint();
					}
				}

				return true;
			}

			return false;
		}

		private void CreateBuildSettings()
		{
			CIBuildSettings ciBuildSettings = CreateInstance<CIBuildSettings>();
			// create the folder if it doesn't exist
			if (!AssetDatabase.IsValidFolder("Assets/SimpleUnityCI"))
			{
				AssetDatabase.CreateFolder("Assets", "SimpleUnityCI");
			}

			AssetDatabase.CreateAsset(ciBuildSettings, "Assets/SimpleUnityCI/CIBuildSettings.asset");
			AssetDatabase.SaveAssets();
			AssetDatabase.Refresh();
			RefreshBuildSettingsExists();
		}

		public void Build()
		{
			// make a request to the build server with the buildsettings as the post body
			CIBuildSettings ciBuildSettings = (CIBuildSettings)buildSettingsField.value;

			ciBuildSettings.buildServer = ciBuildSettings.buildServer.TrimEnd('/');
			string url = ciBuildSettings.buildServer + "/build";
			Debug.Log(url);
			Debug.Log(JsonConvert.SerializeObject(ciBuildSettings.ToDict()));
			UnityWebRequest www = UnityWebRequest.Post(url, JsonConvert.SerializeObject(ciBuildSettings.ToDict()), "application/json");
			www.SendWebRequest();
		}
	}
}
#endif