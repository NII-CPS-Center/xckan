
export function pathOf(path: string): string {
    let match = path.match(/\.[^_]([^:]+):/)
    if(match) {
        let matchStr = path.substring(match.index!, match[0].length)
        path = path.replace(matchStr, matchStr.replace(/_/g, '__').replace(/____/g, '__'))
    }
    return path
}