import "../../designs/TextBox.css"

type Message = {
    message: string
}

function TextBoxPanel(
    props: Message
)
{
    return (
        <div className="textBox">
            {props.message}
        </div>
    )
}
export default TextBoxPanel