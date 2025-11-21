export default async function getPublicIp(): Promise<string | undefined> {
  try {
    const res = await fetch("https://api.ipify.org?format=json");
    const data = (await res.json()) as { ip: string };

    console.log(`Detected public IP: ${data.ip}`);

    return data.ip;
  } catch (error) {
    console.warn("Failed to fetch public IP.");

    return undefined;
  }
}
