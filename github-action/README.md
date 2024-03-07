# SimpleUnityCI GitHub Action

This github action calls the POST endpoint to build on the specified server, then polls the task log once a second until it completes or a timeout occurs. 

## Building

1. `npm run build`
2. Upload the files and a tag to github:
   1. `git commit -am "new stuff"`
   2. `git tag v16`
   3. `git push`
   4. `git push --tags`